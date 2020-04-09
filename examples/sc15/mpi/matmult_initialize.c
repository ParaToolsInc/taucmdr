#include "matmult_initialize.h"

void initialize(double **matrix, int rows, int cols) {
  int i,j;
  {
    //set_num_threads();
    /*** Initialize matrices ***/
    for (i=0; i<rows; i++) {
      for (j=0; j<cols; j++) {
        matrix[i][j]= i+j;
      }
    }
  }
}
