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
 *  reduce.cc
 *  20 May 2013
 *
 */

#include <iostream>
#include <world/world.h>

const int size = 300000000;

double reduce(register double* first, register double* const last) {
  double value = 0.0;
  for(;first != last; ++first)
    value += *first;

  return value;
}

double sum(double left, double right) {
  return left + right;
}

madness::Future<double> task_reduce(madness::World* world,
    double* first, double* last, const int block_size) {
  if ((last - first) <= block_size) {
    return madness::Future<double>(reduce(first, last));
  } else {
    double* middle = first + ((last - first) / 2);

    madness::Future<double>  leftsum =
        world->taskq.add(& task_reduce, world, first, middle,
        block_size, madness::TaskAttributes::hipri());
    madness::Future<double> rightsum =
        task_reduce(world, middle, last, block_size);
    return world->taskq.add(& sum, leftsum, rightsum,
        madness::TaskAttributes::hipri());
  }
}

int main(int argc, char** argv) {
  madness::initialize(argc,argv);
  madness::World world(SafeMPI::COMM_WORLD);

  // Allocate initialize vectors
  double* x = new double[size];
  std::fill_n(x, size, 1.0);

  // Do serial reduce
  const double serial_start = madness::wall_time();
  reduce(x, x + size);
  const double serial_time = madness::wall_time() - serial_start;

  // Output serial results
  std::cout << "Serial Time = " << serial_time << "\n\n";

  // Iterate over different block sizes
  std::cout << "Block size\tTime\t\tSpeedup"
      << "\n---------------------------------------\n";
  for(int block_size = 8; block_size < size; block_size *= 2) {

    // Do axpy in tasks with units of block_size elements
    const double start = madness::wall_time(); // Start time
    madness::Future<double> value =
        task_reduce(& world, x, x + size, block_size);
    // Wait for all tasks to finish (and process tasks)
    value.get();
    const double time = madness::wall_time() - start; // End time

    // Display results
    std::cout << " " << block_size << "     \t"
        << time << "\t" << serial_time / time << "\n";
  }

  delete [] x;

  madness::finalize();
  return 0;
}

