#include <stdlib.h>

double drvRandom(double upper_limit)
{
    return (double)rand() / RAND_MAX * upper_limit;
}
