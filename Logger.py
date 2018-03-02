from SimulationDict import LogLevel
from time import strftime
from sys import stderr

def log( message, level=LogLevel.DEBUG, flush=False ):
  if ( level >= LogLevel.DEBUG ):
    print( "%s %s %s" % ( strftime("%Y%m%d %H:%M:%S"), level.name, message ), flush=flush, file=stderr )
