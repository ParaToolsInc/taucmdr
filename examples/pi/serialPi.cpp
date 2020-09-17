#include <iostream>
#include <stdlib.h>

#include <math.h>
#include <climits>

// This example is adapted from "Using MPI, second edition"
// by Gropp, Lusk, and Skellum



int computeRandom()
{
    return random();
}

double runWorker()
{
    const int numRands = 1000;
    int* rands = new int[ numRands ];


    double x;
    double y;
    bool notDone = true;
    int in = 0;
    int out = 0;
    double epsilon = 0.00000001;
    double error;
    double Pi;

    while ( notDone )
    {
       for ( int i = 0; i < numRands; ) // build up a set of random numbers
       {
           rands[i] = computeRandom();
           if ( rands[i] <= INT_MAX ) ++i;
       }

        for ( int i = 0; i < numRands; ) //work on the set of random numbers
        {
            x = (((double)(rands[i++]))/(double)(INT_MAX)) * 2 - 1;
            y = (((double)(rands[i++]))/(double)(INT_MAX)) * 2 - 1;
            if (( x*x + y*y ) < 1.0 ) ++in;
            else ++out;
        }

        Pi = (4.0 * in) / ( in + out );
        error = fabs( Pi - 3.141592653589793238462643 );
        notDone = ( (error > epsilon) && (in + out) < 10000000 );
    }

    delete[] rands;
    return Pi;
 }

int main( int argc, char* argv[] )
{
    double pi;
    pi = runWorker( );

        std::cout << "Pi is " << pi << std::endl;

}
