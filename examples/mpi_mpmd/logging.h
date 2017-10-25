#ifndef __LOGGING_H__
#define __LOGGING_H__

#define msg(FMT, ...) printf("[%s:%d %d/%d] " FMT, __FILE__, __LINE__, WORLD_RANK, WORLD_SIZE, ## __VA_ARGS__)

extern int WORLD_RANK;
extern int WORLD_SIZE;

void init_logging();

#endif
