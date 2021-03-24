#!/usr/bin/env python
# Program written by Devin Shende on August 5th 2018

def first_prime_after(x):
    import math
    current = x + 1
    sqrtno = math.sqrt(current)
    while True:
        # search for primes starting at x until it finds one
        # break once found a prime
        for potential_factor in range(2, current):
            # start at 2 because 1 will always be a factor
            # go all the way up to the sqrt of current looking for a factor
            if current % potential_factor == 0:
                # Found factor. not prime
                break  # move on to next number
            elif potential_factor >= sqrtno:
                print(f"The first prime number after {x} is {current}")
                return current
        current += 1


first_prime_after(10000000)
