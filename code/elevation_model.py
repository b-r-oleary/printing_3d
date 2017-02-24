import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d

from scipy import ndimage
import numpy as np

# numpy-stl requirements
from stl import mesh
from stl.stl import BINARY
from itertools import product

import os

from . import verbosify

class ElevationModel(object):
    """
    This is an object that is used to create an STL file 
    from a digital elevation map image input.
    """
    
    # a set of four pixels in a square should be mapped onto
    # two triangles in an STL - these are defined h
    _upper = np.array([[0, 0],
                       [0, 1],
                       [1, 0]])

    _lower = np.array([[0, 1],
                       [1, 1],
                       [1, 0]])
    
    # use the stl extension when saving an STL file.
    extension = "stl"
    
    def __init__(self,
                 filename,
                 resolution_factor=1.0,
                 radius=10.0,
                 base=0,
                 scale=1.0,
                 zscale=1.0,
                 verbose=True):
        """
        
        *inputs*
        filename (str) path to file with digital elevation map image
        resolution_factor (float >=1) factor by which to reduce the resolution
        radius (float) assuming a digital elevation map corresponding to a sphere, the radius of that sphere
        base (float) the amount of base to apply to the elevation map beyond the radius
        scale (float) the factor by which to scale the x, y, and z coordinates
        zscale (float) factor by which to scale the z coordinate to exaggerate features
        verbose (bool) whether or not to print computational updates to the console
        """
        
        self.filename = filename
        self.resolution_factor = resolution_factor
        self.radius = radius
        self.base = base
        self.scale = scale
        self.zscale = zscale
        self._counter = None
        self._image = None
        self.image = None
        self.verbose = verbose
    
    @verbosify
    def load(self,
             announce="loading the image from file"):
        """
        load the image input memory, extract the size of the image
        and reduce the resolution of the image if requested
        """
        self._image = ndimage.imread(self.filename)
        self._x, self._y = self._image.shape
        self.reduce_resolution()
        
    def reduce_resolution(self):
        """
        reduce the resolution of self._image by factor self.resolution_factor
        resulting in self.image
        """
        x_subset = (self.resolution_factor * np.arange(self._x // self.resolution_factor)).astype(int)
        y_subset = (self.resolution_factor * np.arange(self._y // self.resolution_factor)).astype(int)
        
        subset = self._image
        subset = subset[x_subset, :]
        subset = subset[:, y_subset]
        
        self.image = subset
        self.x, self.y = self.image.shape
        
        
    def number_of_triangles(self):
        "return the number of STL triagles required to build the STL"
        return (2 * (self.x - 1) * (self.y - 1)       # number of surface triangles
                + ( (self.x - 1) + (self.y - 1)) * 4  # number of side triangles
                + 2 )                                 # number of base triangles
        
    def get_template_triangles(self, handedness="r"):
        """
        the STL triangles have the convention that the vertices in the triangle
        must be listed with a handedness pointing outward from the solid object.
        This method swaps the handedness of the template self._upper and self._lower
        triangles.
        """
        if   handedness == "r":
            permute = [0, 1, 2]
        elif handedness == "l":
            permute = [0, 2, 1]
        else:
            raise IOError("handedness not recognized (must be 'r' or 'l')")
            
        return [
                self._upper[permute, :],
                self._lower[permute, :],
               ]
    
    def counter(self):
        """
        a simple counter method for keeping track of the current triangle index
        """
        if self._counter is None:
            self._counter = -1
        self._counter += 1
        return self._counter
        
    def generate_stl(self):
        """
        generate the STL in memory:
        - load the image (and reduce resolution)
        - initialize a numpy array for holding the STL triangles
        - initialize the counter
        - insert the STL triangles
            - generate the surface
            - generate the sides
            - generate the base
        - then rescale the resulting STL array by factors input into __init__
        """
        if self.verbose:
            print("generating an STL from the digital elevation map: " + self.filename)
        
        self.load()
        
        self.elevation = mesh.Mesh(
                            np.zeros(self.number_of_triangles(), 
                            dtype=mesh.Mesh.dtype)
                         )
        
        self._counter = None
        
        self.generate_surface(handedness="l")
        self.generate_side("x",  0, handedness="l")
        self.generate_side("x", -1, handedness="r")
        self.generate_side("y",  0, handedness="r")
        self.generate_side("y", -1, handedness="l")
        self.generate_base(handedness="r")
        
        self.rescale()
    
    @verbosify
    def generate_surface(self, handedness="l",
                         announce="generating the surface"):
        "generate the STL surface with specified handedness for image self.image"

        array = self.image
        for i, j in product(range(self.x - 1),
                            range(self.y - 1)):
    
            for triangle in self.get_template_triangles(handedness=handedness):
                m = self.counter()
                for n, (k, l) in enumerate(triangle):
                    self.elevation.vectors[m][n] = np.array(
                                          [i + k, j + l, array[i + k, j + l]]
                                          )
    
    @verbosify
    def generate_side(self, dimension, index, handedness="l",
                      announce="generating a side"):
        """
        construct one of the 4 sides of the STL object
        
        *inputs*
        dimension (str - "x" or "y") corresponding to the dimension alon which to construct the side
        index (0, or -1) indicating the index of the edge along the not specified dimension
        """
        
        if dimension == "x":
            array = np.array([np.zeros(self.image[:, index].shape), self.image[:, index]]).T
            length = self.x - 1
        elif dimension == "y":
            array = np.array([np.zeros(self.image[index, :].shape), self.image[index, :]]).T
            length = self.y - 1
        else:
            raise IOError("dimension must be 'x' or 'y'")

        for i in range(length):
            for triangle in self.get_template_triangles(handedness=handedness):
                m = self.counter()
                for n, (k, l) in enumerate(triangle):
                    if dimension == "x":
                        vector = [i + k, - index * (self.y - 1), array[i + k, l]]
                    else:
                        vector = [- index * (self.x - 1), i + k, array[i + k, l]]
                    self.elevation.vectors[m][n] = np.array(
                                            vector
                                            )
    @verbosify
    def generate_base(self, handedness="r",
                      announce="generating the base"):
        "generate the base (only two triangles!)"

        for triangle in self.get_template_triangles(handedness=handedness):
            m = self.counter()
            for n, (k, l) in enumerate(triangle):
                self.elevation.vectors[m][n] = np.array(
                                            [k * (self.x - 1), l * (self.y - 1), 0]
                                            )
                
    def rescale(self):
        """rescale the stl with the appropriate units and scaling factors"""
        self.elevation.vectors[:,:,0] = self.scale * 1 * np.pi * self.radius * self.elevation.vectors[:,:,0] / self.elevation.vectors[:,:,0].max()
        self.elevation.vectors[:,:,1] = self.scale * 2 * np.pi * self.radius * self.elevation.vectors[:,:,1] / self.elevation.vectors[:,:,1].max()
        self.elevation.vectors[:,:,2] = self.zscale * self.scale * (self.elevation.vectors[:,:,2]) + self.base
                
    def plot(self):
        "plot the image in 2D"
        if self.image is None:
            self.load()
        plt.imshow(self.image)
    
    @verbosify
    def save(self, filename=None, mode=BINARY,
             announce="saving STL to file"):
        "save the STL to file in binary format by default"
        
        if filename is None:
            path, file = os.path.split(self.filename)
            file = '.'.join(file.split('.')[:-1] + [self.extension])
            filename = os.path.join(path, file)
            
        self.elevation.save(filename, mode=mode)
        
    @verbosify
    def plot3d(self, va=45, ha=45,
               announce="plotting the resulting STL in 3D"):
        """
        plot the STL in 3D 
        (do not do this if it is large - 
        matplotlib can't handle it - 
        just open the stl with a 3d object viewer program)
        """

        # Create a new plot
        figure = plt.figure()
        axes = mplot3d.Axes3D(figure)

        # Render the cube faces
        axes.add_collection3d(
            mplot3d.art3d.Poly3DCollection(self.elevation.vectors)
        )

        ax = plt.gca()
        
        ax.set_xlim([self.elevation.vectors[:,:,0].min(),
                     self.elevation.vectors[:,:,0].max()])
        ax.set_ylim([self.elevation.vectors[:,:,1].min(),
                     self.elevation.vectors[:,:,1].max()])
        ax.set_zlim([self.elevation.vectors[:,:,2].min(),
                     self.elevation.vectors[:,:,2].max()])
        
        ax.view_init(va, ha)
        return