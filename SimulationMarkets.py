#!/usr/bin/python

import csv
from enum import Enum
from random import random
from Logger import log
from SimulationMarketPhases import marketPhaseTransitions, MarketPhases, marketPhaseTransition
from SimulationDict import LogLevel

defaultMarketPhaseTransitions = {
  MarketPhases.CLOSED : marketPhaseTransition( 0.1, MarketPhases.PREOPEN ),
  MarketPhases.PREOPEN: marketPhaseTransition( 0.1, MarketPhases.OAPRINT ),
  MarketPhases.OAPRINT: marketPhaseTransition( 1.0, MarketPhases.OPEN ),
  MarketPhases.OPEN: marketPhaseTransition( 0.01, MarketPhases.PRECLOSE ),
  MarketPhases.PRECLOSE: marketPhaseTransition( 0.1, MarketPhases.CAPRINT ),
  MarketPhases.CAPRINT: marketPhaseTransition( 1.0, MarketPhases.CLOSED )
 }

class Market( object ):
  def __init__( self, mic, name, country, marketPhases=defaultMarketPhaseTransitions ):
    self.mic = mic
    self.name = name
    self.country = country
    self.currentPhase=MarketPhases.CLOSED
    self.marketPhases=marketPhases

  def toString( self ):
    return "%s, %s, %s" % ( self.name, self.mic, self.country )

  def checkMarketPhase( self ):
    nextTransition=self.marketPhases[ self.currentPhase ]
    if( random() <= nextTransition.probability ):
      log( "%s is now %s" % ( self.mic, nextTransition.nextPhase.value.description ), LogLevel.INFO )
      self.currentPhase=nextTransition.nextPhase

def loadMarketDefinitions( marketDefinitionFile = 'Markets.dat' ):
  markets = {}
  # TODO handle exception when file read fails.
  for row in csv.DictReader( open( marketDefinitionFile ) ):
    markets[ row['ExchangeId'] ] = Market(  row['ExchangeId'], row['Description'], row['Country'], marketPhaseTransitions[ row['PhaseTransitions'] ] )
  Markets = Enum( 'Markets', markets ) 

  return Markets
Markets = loadMarketDefinitions()

def main():
  for m in Markets:
    print( m )


if __name__ == "__main__":
  main()
