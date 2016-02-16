CXX = g++
CXXFLAGS = 

LD = $(CXX)
LDFLAGS	= 
LIBS =

RM 	      	= /bin/rm -f

TARGET	      	= simple

##############################################

all:		$(TARGET)	

install: 	$(TARGET)

$(TARGET):	$(TARGET).o
	$(CXX) $(LDFLAGS) $(TARGET).o -o $@ $(LIBS)

$(TARGET).o : $(TARGET).cpp
	$(CXX) $(CFLAGS) -c $(TARGET).cpp

clean: 	
	$(RM) $(TARGET).o $(TARGET)
##############################################
