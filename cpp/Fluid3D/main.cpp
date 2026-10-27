#include <cstdio>
#include <iostream>
#include <sstream>
#include <fstream>
#include <string>
#include <cfloat>
#include <cstdlib>

#include "fluidsim.h"
#include "array3_utils.h"

using namespace std;

int grid_resolution = 60;
float timestep = 0.01f;
int frame = 0;

float grid_width = 1;

FluidSim sim;

float sphere_phi(const Vec3f& position, const Vec3f& centre, float radius) {
   return (dist(position,centre) - radius);
}

Vec3f c0(0.5f,0.5f,0.5f);
float rad0 = 0.35f;

float boundary_phi(const Vec3f& position) {
   return -sphere_phi(position, c0, rad0);
}

float liquid_phi(const Vec3f& position) {
   return sphere_phi(position, Vec3f(0.55f, 0.55f, 0.4f), 0.23f);
}

void export_particles(string path, int frame, const std::vector<Vec3f>& particles, float radius);

//Main testing code
//-------------
int main(int argc, char **argv)
{
   
   if(argc != 2 && argc != 3){
      cerr << "Usage: solver <output-folder/> [frames]" << endl;
      cerr << "  frames defaults to 1000. The folder path should end with a separator." << endl;
      return 1;
   }

   string outpath(argv[1]);
   int frame_count = 1000;
   if(argc == 3){
      frame_count = atoi(argv[2]);
      if(frame_count < 1){
         cerr << "frames must be >= 1" << endl;
         return 1;
      }
   }
   
   printf("Initializing data\n");
   sim.initialize(grid_width, grid_resolution, grid_resolution, grid_resolution);
   
   printf("Initializing boundary\n");
   sim.set_boundary(boundary_phi);
   
   printf("Initializing liquid\n");
   sim.set_liquid(liquid_phi);
      
   printf("Exporting initial data\n");
   export_particles(outpath, 0, sim.particles, sim.particle_radius);

   for(frame = 1; frame < frame_count; ++frame) {
      printf("--------------------\nFrame %d\n", frame);
      
      //Simulate
      printf("Simulating liquid\n");
      sim.advance(timestep);
      
      printf("Exporting particle data\n");
      export_particles(outpath, frame, sim.particles, sim.particle_radius);
   }

   return 0;
}


void export_particles(string path, int frame, const std::vector<Vec3f>& particles, float radius) {
   //Write the output
   
   std::stringstream strout;
   strout << path << "particles_" << frame << ".txt";
   string filepath = strout.str();
   
   ofstream outfile(filepath.c_str());
   //write vertex count and particle radius
   outfile << particles.size() << " " << radius << std::endl;
   //write vertices
   for(unsigned int i = 0; i < particles.size(); ++i)
      outfile << particles[i][0] << " " << particles[i][1] << " " << particles[i][2] << std::endl;

   std::cout << "Writing to: " << filepath << std::endl; 
   outfile.close();
}


