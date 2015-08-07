/*
 *  Copyright (C) 2013 Virginia Tech
 *
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 *  Justus Calvin
 *  Department of Chemistry, Virginia Tech
 *
 *  axpy.cc
 *  20 May 2013
 *
 */

#include <iostream>
#include <world/world.h>

const int size = 300000000;

void axpy(double* y, const double* x, const double a, const int n) {
  for(int i = 0; i < n; ++i)
    y[i] += a * x[i];
}

int main(int argc, char** argv) {
    madness::initialize(argc,argv);
    madness::World world(SafeMPI::COMM_WORLD);

    // Allocate initialize vectors
    double* x = new double[size];
    std::fill_n(x, size, 1.0);
    double* y = new double[size];
    std::fill_n(y, size, 0.0);
    const double a = 2.0;

    // Do serial axpy
    const double serial_start = madness::wall_time();
    axpy(y, x, a, size);
    const double serial_time = madness::wall_time() - serial_start;

    // Output serial results
    std::cout << "Serial Time = " << serial_time << "\n\n";

    // Iterate over different block sizes
    std::cout << "Block size\tTime\t\tSpeedup"
        << "\n---------------------------------------\n";
    for(int block_size = 8; block_size < size; block_size *= 2) {

      // Do axpy in tasks with units of block_size elements
      const double start = madness::wall_time(); // Start time
      int i = 0;
      const int end = size - (size % block_size);
      for(i = 0; i < end; i += block_size)
        world.taskq.add(& axpy, y+i, x+i, a, block_size);
      if(i < size) // The last task does whatever is remaining
        world.taskq.add(& axpy, y+i, x+i, a, size%block_size);

      // Wait for all tasks to finish (and process tasks)
      world.taskq.fence();
      const double time = madness::wall_time() - start; // End time

      // Display results
      std::cout << " " << block_size << "     \t"
          << time << "\t" << serial_time / time << "\n";
    }

    madness::finalize();
    return 0;
}
