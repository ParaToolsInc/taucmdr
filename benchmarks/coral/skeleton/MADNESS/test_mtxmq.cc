/*
  This file is part of MADNESS.

  Copyright (C) 2007,2010 Oak Ridge National Laboratory

  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 2 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program; if not, write to the Free Software
  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

  For more information please contact:

  Robert J. Harrison
  email: rjharrison@gmail.com

  $Id$
*/

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <complex>

/* MPI_Wtime is the only function used... */
#include <mpi.h>

#include <cblas.h>
#include <mtxmq.h>

#define TIME_DGEMM
#define ALIGNMENT 128

using namespace madness;

#ifdef TIME_DGEMM
void mTxm_dgemm(long ni, long nj, long nk, double* c, const double* a, const double*b ) {
  double one=1.0;
  madness::cblas::gemm(madness::cblas::NoTrans,madness::cblas::Trans,nj,ni,nk,one,b,nj,a,ni,one,c,nj);
}
#endif

double ran()
{
  static unsigned long seed = 76521;

  seed = seed*1812433253 + 12345;

  return ((double) (seed & 0x7fffffff)) * 4.6566128752458e-10;
}

void ran_fill(int n, double *a) {
    while (n--) *a++ = ran();
}

void mTxm(long dimi, long dimj, long dimk,
          double* c, const double* a, const double* b) {
    int i, j, k;
    for (k=0; k<dimk; ++k) {
        for (j=0; j<dimj; ++j) {
            for (i=0; i<dimi; ++i) {
                c[i*dimj+j] += a[k*dimi+i]*b[k*dimj+j];
            }
        }
    }
}

void crap(double rate, double fastest, double start) {
    if (rate == 0) printf("darn compiler bug %e %e %lf\n",rate,fastest,start);
}


void timer(const char* s, long ni, long nj, long nk, double *a, double *b, double *c) {

  int rank;
  MPI_Comm_rank(MPI_COMM_WORLD, &rank);
  double fastest=0.0, fastest_dgemm=-1.0;
  double nflop = 2.0*ni*nj*nk;
  long loop;
  MPI_Barrier(MPI_COMM_WORLD);
  for (loop=0; loop<30; ++loop) {
    double rate;
    double start = MPI_Wtime();
    mTxmq(ni,nj,nk,c,a,b);
    start = MPI_Wtime() - start;
    rate = 1.e-9*nflop/start;
    crap(rate,fastest,start);
    if (rate > fastest) fastest = rate;
  }
  MPI_Barrier(MPI_COMM_WORLD);
#ifdef TIME_DGEMM
  for (loop=0; loop<30; ++loop) {
    double rate;
    double start = MPI_Wtime();
    mTxm_dgemm(ni,nj,nk,c,a,b);
    start = MPI_Wtime() - start;
    rate = 1.e-9*nflop/start;
    crap(rate,fastest_dgemm,start);
    if (rate > fastest_dgemm) fastest_dgemm = rate;
  }
  MPI_Barrier(MPI_COMM_WORLD);
#endif
  if (rank==0)
    printf("%20s %3ld %3ld %3ld %8.2f %8.2f\n",s, ni,nj,nk, fastest, fastest_dgemm);
}

void trantimer(const char* s, long ni, long nj, long nk, double *a, double *b, double *c) {
  int rank;
  MPI_Comm_rank(MPI_COMM_WORLD, &rank);
  double fastest=0.0, fastest_dgemm=-1.0;
  double nflop = 3.0*2.0*ni*nj*nk;
  long loop;
  MPI_Barrier(MPI_COMM_WORLD);
  for (loop=0; loop<30; ++loop) {
    double rate;
    double start = MPI_Wtime();
    mTxmq(ni,nj,nk,c,a,b);
    mTxmq(ni,nj,nk,a,c,b);
    mTxmq(ni,nj,nk,c,a,b);
    start = MPI_Wtime() - start;
    rate = 1.e-9*nflop/start;
    crap(rate,fastest,start);
    if (rate > fastest) fastest = rate;
  }
  MPI_Barrier(MPI_COMM_WORLD);
#ifdef TIME_DGEMM
  for (loop=0; loop<30; ++loop) {
    double rate;
    double start = MPI_Wtime();
    mTxm_dgemm(ni,nj,nk,c,a,b);
    mTxm_dgemm(ni,nj,nk,a,c,b);
    mTxm_dgemm(ni,nj,nk,c,a,b);
    start = MPI_Wtime() - start;
    rate = 1.e-9*nflop/start;
    crap(rate,fastest_dgemm,start);
    if (rate > fastest_dgemm) fastest_dgemm = rate;
  }
  MPI_Barrier(MPI_COMM_WORLD);
#endif
  if (rank==0)
    printf("%20s %3ld %3ld %3ld %8.2f %8.2f\n",s, ni,nj,nk, fastest, fastest_dgemm);
}

int main(int argc, char * argv[]) {
    const long nimax=30*30;
    const long njmax=100;
    const long nkmax=100;
    long ni, nj, nk, i, m;
    double *a, *b, *c, *d;

    int provided, rank, size;
    MPI_Init_thread(&argc, &argv, MPI_THREAD_SINGLE, &provided);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if (rank==0)
      printf("Running MADNESS mTxm test on %d procs at the same time \n", size);

    posix_memalign((void **) &a, ALIGNMENT, nkmax*nimax*sizeof(double));
    posix_memalign((void **) &b, ALIGNMENT, nkmax*njmax*sizeof(double));
    posix_memalign((void **) &c, ALIGNMENT, nimax*njmax*sizeof(double));
    posix_memalign((void **) &d, ALIGNMENT, nimax*njmax*sizeof(double));

    ran_fill(nkmax*nimax, a);
    ran_fill(nkmax*njmax, b);

/*     ni = nj = nk = 2; */
/*     for (i=0; i<ni*nj; ++i) d[i] = c[i] = 0.0; */
/*     mTxm (ni,nj,nk,c,a,b); */
/*     mTxmq(ni,nj,nk,d,a,b); */
/*     for (i=0; i<ni; ++i) { */
/*       long j; */
/*       for (j=0; j<nj; ++j) { */
/* 	printf("%2ld %2ld %.6f %.6f\n", i, j, c[i*nj+j], d[i*nj+j]); */
/*       } */
/*     } */
/*     return 0; */

    if (rank==0)
      printf("Starting to test ... \n");
    for (ni=2; ni<60; ni+=2) {
        for (nj=2; nj<100; nj+=6) {
            for (nk=2; nk<100; nk+=6) {
                for (i=0; i<ni*nj; ++i) d[i] = c[i] = 0.0;
                mTxm (ni,nj,nk,c,a,b);
                mTxmq(ni,nj,nk,d,a,b);
                for (i=0; i<ni*nj; ++i) {
                    double err = std::abs(d[i]-c[i]);
                    /* This test is sensitive to the compilation options.
                       Be sure to have the reference code above compiled
                       -msse2 -fpmath=sse if using GCC.  Otherwise, to
                       pass the test you may need to change the threshold
                       to circa 1e-13.
                    */
                    if (err > 1e-15) {
                        printf("test_mtxmq: error %ld %ld %ld %e\n",ni,nj,nk,err);
                        exit(1);
                    }
                }
            }
        }
    }
    if (rank==0)
      printf("... OK!\n");

    for (ni=2; ni<60; ni+=2) timer("(m*m)T*(m*m)", ni,ni,ni,a,b,c);
    for (m=2; m<=30; m+=2) timer("(m*m,m)T*(m*m)", m*m,m,m,a,b,c);
    for (m=2; m<=30; m+=2) trantimer("tran(m,m,m)", m*m,m,m,a,b,c);
    for (m=2; m<=20; m+=2) timer("(20*20,20)T*(20,m)", 20*20,m,20,a,b,c);

    MPI_Finalize();

    return 0;
}

