#!/usr/bin/python

from enum import Enum
from types import MethodType
from random import random, seed
from SimulationMarketLoad import Markets, MarketPhases

seed( None )

def main():
  print( "Configured Markets:" )
  for exchange in Markets:
    print( "%s: %s" % ( exchange, exchange.value.toString() ) )
    exchange.value.checkMarketPhase()
  

if __name__ == "__main__":
  main()
