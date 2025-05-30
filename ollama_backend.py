from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import json
import logging
from ollama import chat, ChatResponse
from tools.custom_scrapper import search_and_scrape
from tools.custom_yfinance import get_stock_summary
from tools.custom_memories import store_memory, search_memory
from tool_schema import tools_schema 
from tool_schema import tools_prompt
import ast
import time

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# ------------------------ SETUP ------------------------

available_functions = {
    'search_and_scrape': search_and_scrape,
    'skip_tools': lambda: "Answer provided directly by AI without external tools.",
    'get_stock_summary': get_stock_summary,
    'store_memory': store_memory,
    "search_memory": search_memory
}

logging.basicConfig(level=logging.INFO, filename="tool_logs.txt", filemode="a",
                    format="%(asctime)s - %(levelname)s - %(message)s")

emoji_map = {
    "get_stock_summary": "📈",
    "search_and_scrape": "🌐",
    "skip_tools": "💡",
    "store_memory": "💾",
    "search_memory": "📝"
}

def stream_ollama_response(model: str, messages: list):
    """Generator function for streaming responses"""
    for chunk in chat(model, messages=messages, stream=True):
        if chunk and getattr(chunk, "message", None):
            yield chunk.message.content

# ------------------------ API ROUTES ------------------------

@app.route('/api/suggestions', methods=['GET'])
def get_suggestions():
    """Get quick prompt suggestions"""
    suggestions = [
        "What's the stock price of RELIANCE?",
        "Show me latest news Tata motors.",
        "What's the current weather in Mumbai?",
        "Compare and do analysis of kotak and hdfc bank with latest price in table format"
    ]
    return jsonify({"suggestions": suggestions})

@app.route('/api/chat', methods=['POST'])
def chat_endpoint():
    """Main chat endpoint that processes queries and returns responses"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({"error": "Query is required"}), 400

        # Prepare initial messages
        initial_messages = [
            {'role': 'system', 'content': tools_prompt.tool_system_prompt},
            {'role': 'user', 'content': query}
        ]

        tools = [
            tools_schema.web_search_tool, 
            tools_schema.skip_tool, 
            tools_schema.stock_fetch_tool, 
            tools_schema.store_memory_tool, 
            tools_schema.search_memory_tool
        ]

        # Get initial response from Ollama
        try:
            response: ChatResponse = chat('llama3.2', messages=initial_messages, tools=tools)
            logging.info("Initial chat call successful")
        except Exception as e:
            logging.error(f"Chat model failed: {e}")
            return jsonify({"error": f"Chat model failed: {str(e)}"}), 500

        result = {
            "query": query,
            "tool_calls": [],
            "final_response": "",
            "status": "success"
        }

        if response.message.tool_calls:
            for tool in response.message.tool_calls:
                func_name = tool.function.name
                args = tool.function.arguments if isinstance(tool.function.arguments, dict) else {}

                tool_result = {
                    "function_name": func_name,
                    "arguments": args,
                    "emoji": emoji_map.get(func_name, "🔧"),
                    "output": None,
                    "error": None
                }

                # Validate and process inputs
                validation_error = validate_tool_args(func_name, args)
                if validation_error:
                    tool_result["error"] = validation_error
                    result["tool_calls"].append(tool_result)
                    continue

                # Execute the function
                func = available_functions.get(func_name)
                if not func:
                    tool_result["error"] = f"Function `{func_name}` not found."
                    result["tool_calls"].append(tool_result)
                    continue

                try:
                    output = func(**args)
                    tool_result["output"] = output
                    
                    # Generate final response based on tool output
                    final_response = generate_final_response(query, func_name, output, initial_messages)
                    result["final_response"] = final_response

                except Exception as e:
                    tool_result["error"] = f"Error executing `{func_name}`: {str(e)}"
                    logging.error(f"Error executing {func_name}: {e}")

                result["tool_calls"].append(tool_result)

        else:
            # No tool calls, generate direct response
            result["final_response"] = response.message.content

        return jsonify(result)

    except Exception as e:
        logging.error(f"Chat endpoint error: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """Streaming chat endpoint"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({"error": "Query is required"}), 400

        def generate():
            try:
                # Process the query similar to the main chat endpoint
                initial_messages = [
                    {'role': 'system', 'content': tools_prompt.tool_system_prompt},
                    {'role': 'user', 'content': query}
                ]

                tools = [
                    tools_schema.web_search_tool, 
                    tools_schema.skip_tool, 
                    tools_schema.stock_fetch_tool, 
                    tools_schema.store_memory_tool, 
                    tools_schema.search_memory_tool
                ]

                response: ChatResponse = chat('llama3.2', messages=initial_messages, tools=tools)
                
                if response.message.tool_calls:
                    for tool in response.message.tool_calls:
                        func_name = tool.function.name
                        args = tool.function.arguments if isinstance(tool.function.arguments, dict) else {}

                        # Send tool selection info
                        yield f"data: {json.dumps({'type': 'tool_selected', 'function': func_name, 'args': args})}\n\n"

                        # Validate and execute tool
                        validation_error = validate_tool_args(func_name, args)
                        if validation_error:
                            yield f"data: {json.dumps({'type': 'error', 'message': validation_error})}\n\n"
                            continue

                        func = available_functions.get(func_name)
                        if not func:
                            yield f"data: {json.dumps({'type': 'error', 'message': f'Function {func_name} not found'})}\n\n"
                            continue

                        try:
                            # Execute tool
                            yield f"data: {json.dumps({'type': 'tool_executing', 'function': func_name})}\n\n"
                            output = func(**args)
                            yield f"data: {json.dumps({'type': 'tool_output', 'function': func_name, 'output': output})}\n\n"

                            # Generate and stream final response
                            refinement_messages = prepare_refinement_messages(query, func_name, output, initial_messages)
                            
                            yield f"data: {json.dumps({'type': 'response_start'})}\n\n"
                            
                            for chunk in stream_ollama_response("llama3.2", refinement_messages):
                                if chunk:
                                    yield f"data: {json.dumps({'type': 'response_chunk', 'content': chunk})}\n\n"
                            
                            yield f"data: {json.dumps({'type': 'response_end'})}\n\n"

                        except Exception as e:
                            yield f"data: {json.dumps({'type': 'error', 'message': f'Error executing {func_name}: {str(e)}'})}\n\n"

                else:
                    # No tool calls, stream direct response
                    yield f"data: {json.dumps({'type': 'response_start'})}\n\n"
                    for chunk in stream_ollama_response("llama3.2", initial_messages):
                        if chunk:
                            yield f"data: {json.dumps({'type': 'response_chunk', 'content': chunk})}\n\n"
                    yield f"data: {json.dumps({'type': 'response_end'})}\n\n"

            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        return Response(generate(), mimetype='text/plain', headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'text/event-stream'
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/memory', methods=['GET', 'POST', 'DELETE'])
def memory_manager():
    """Memory management endpoint"""
    try:
        if request.method == 'GET':
            # Get all memories (you'll need to implement this in your memory module)
            try:
                memories = search_memory("")  # Get all memories
                return jsonify({"memories": memories})
            except Exception as e:
                return jsonify({"error": f"Failed to retrieve memories: {str(e)}"}), 500

        elif request.method == 'POST':
            data = request.get_json()
            action = data.get('action')

            if action == 'search':
                query = data.get('query', '')
                results = search_memory(query)
                return jsonify({"results": results})

            elif action == 'store':
                memory_data = data.get('memory_data', '')
                tags = data.get('tags', [])
                result = store_memory(memory_data=memory_data, tags=tags)
                return jsonify({"result": result, "message": "Memory stored successfully"})

            else:
                return jsonify({"error": "Invalid action"}), 400

        elif request.method == 'DELETE':
            # Implement memory deletion if your memory module supports it
            data = request.get_json()
            memory_id = data.get('memory_id')
            # You'll need to implement delete_memory function
            return jsonify({"message": "Memory deletion not implemented yet"}), 501

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ------------------------ HELPER FUNCTIONS ------------------------

def validate_tool_args(func_name, args):
    """Validate tool arguments"""
    if func_name == "search_and_scrape":
        if not args.get('query', '').strip():
            return "Empty query passed to search_and_scrape tool."
    
    elif func_name == "get_stock_summary":
        stock_symbols = args.get('stock_symbols', '')
        if isinstance(stock_symbols, list):
            stock_symbols = ','.join(stock_symbols).strip()
        elif isinstance(stock_symbols, str):
            stock_symbols = stock_symbols.strip()
        else:
            stock_symbols = ''
        args['stock_symbols'] = stock_symbols
        if not stock_symbols:
            return "No stock symbols detected."
    
    elif func_name == "store_memory":
        tags = args.get("tags")
        if isinstance(tags, str):
            try:
                tags = ast.literal_eval(tags)
                if not isinstance(tags, list):
                    raise ValueError
                args["tags"] = tags
            except Exception:
                return f"Invalid tags format: {tags}."
        elif tags is not None and not isinstance(tags, list):
            return f"Invalid tags format: {tags}."
    
    return None

def generate_final_response(query, func_name, output, initial_messages):
    """Generate final response based on tool output"""
    output_str = json.dumps(output, indent=2) if not isinstance(output, str) else output
    refinement_messages = prepare_refinement_messages(query, func_name, output_str, initial_messages)
    
    try:
        response = chat('llama3.2', messages=refinement_messages)
        return response.message.content
    except Exception as e:
        logging.error(f"Error generating final response: {e}")
        return f"Tool executed successfully but failed to generate response: {str(e)}"

def prepare_refinement_messages(query, func_name, output_str, initial_messages):
    """Prepare messages for refinement based on tool type"""
    if func_name == "search_memory":
        return [
            {
                'role': 'system',
                'content': (
                    "You are a helpful AI assistant. Your role is to remember and refer to what the user has previously told you. "
                    "The context of the conversation may include entries from memory with the role 'tool', and you should use that information "
                    "to respond appropriately."
                )
            },
            {'role': 'user', 'content': query},
            {'role': 'tool', 'name': func_name, 'content': output_str}
        ]
    
    elif func_name == "store_memory":
        return [
            {'role': 'system', 'content': "You are a helpful AI assistant."},
            {'role': 'user', 'content': f"The user's memory has been updated with: {output_str}"}
        ]
    
    else:
        return initial_messages + [{'role': 'tool', 'name': func_name, 'content': output_str}]

# ------------------------ ERROR HANDLERS ------------------------

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

# ------------------------ MAIN ------------------------

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)