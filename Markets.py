#!/usr/bin/python

from enum import Enum
from types import MethodType
from random import random, seed

seed( None )

class MarketPhase( object ):
  def __init__ ( self, description, tradingAllowed=False, quotingAllowed=False, auctionPrint=False ):
    self.description = description
    self.tradingAllowed = tradingAllowed
    self.quotingAllowed = quotingAllowed
    self.auctionPrint = auctionPrint

class MarketPhases( Enum ):
  CLOSED = MarketPhase( 'Closed' )
  PREOPEN = MarketPhase( 'Pre-Open', quotingAllowed=True )
  OPEN = MarketPhase( 'Continuous Trading', quotingAllowed=True, tradingAllowed=True )
  PRECLOSE = MarketPhase( 'Pre-Close', quotingAllowed=True )
  OAPRINT = MarketPhase( 'Opening Auction', auctionPrint=True )
  CAPRINT = MarketPhase( 'Closing Auction', auctionPrint=True )

class marketPhaseTransition( object ):
  def __init__ (self, probability, nextPhase ):
    self.probability = probability
    self.nextPhase = nextPhase 

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
    #print( "Mkt: %s, Phase is %s, Probability of change: %s" % ( self.mic, self.currentPhase, nextTransition.probability ) )
    if( random() <= nextTransition.probability ):
      print( "%s is now %s" % ( self.mic, nextTransition.nextPhase.value.description ) )
      self.currentPhase=nextTransition.nextPhase

class Markets( Enum ):
  XASX=Market( 'XASX', 'The Australian Securities Exchange', 'Australia' )
  XTKS=Market( 'XTKS', 'The Tokyo Stock Exchange', 'Japan' )

def main():
  print( "Configured Markets:" )
  for exchange in Markets:
    print( "%s: %s" % ( exchange, exchange.value.toString() ) )
    exchange.value.checkMarketPhase()
  

if __name__ == "__main__":
  main()
