from nilearn import plotting, datasets, surface
fsaverage = datasets.fetch_surf_fsaverage()
motor_images = datasets.fetch_neurovault_motor_task()
mesh = surface.load_surf_mesh(fsaverage.pial_right)
map = surface.vol_to_surf(motor_images.images[0], mesh)
fig = plotting.plot_surf_stat_map(mesh, map, hemi='right',
                                  view='lateral', colorbar=True,
                                  threshold=1.2,
                                  bg_map=fsaverage.sulc_right,
                                  engine='plotly')
fig.show()