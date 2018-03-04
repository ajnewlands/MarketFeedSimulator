#!/usr/bin/python

import csv
from enum import Enum
from collections import defaultdict


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
  OPENMORNING = MarketPhase( 'Morning Continuous Trading', quotingAllowed=True, tradingAllowed=True )
  OPENAFTERNOON = MarketPhase( 'Afternoon Continuous Trading', quotingAllowed=True, tradingAllowed=True )
  PRECLOSE = MarketPhase( 'Pre-Close', quotingAllowed=True )
  OAPRINT = MarketPhase( 'Opening Auction', auctionPrint=True )
  CAPRINT = MarketPhase( 'Closing Auction', auctionPrint=True )
  NOONPREOPEN = MarketPhase( 'Noon Pre-Open', quotingAllowed=True )
  BREAK = MarketPhase( 'Mid Day Break' )
  NOONPRECLOSE = MarketPhase( 'Pre-Close', quotingAllowed=True )


class marketPhaseTransition( object ):
  def __init__ (self, probability, nextPhase ):
    self.probability = probability
    self.nextPhase = nextPhase

def loadMarketPhases( marketPhaseDefinitionsFile = 'PhaseTransitions.dat' ):
  transitions = defaultdict( dict )
  for r in csv.DictReader( open( marketPhaseDefinitionsFile ) ):
    name = r['TransitionName']
    currentPhase = r['CurrentPhase']
    nextPhase = r['NextPhase']
    probability = float( r['Probability'] )
    transitions[ name ][ MarketPhases[ currentPhase ] ] = marketPhaseTransition( probability, MarketPhases[ nextPhase ])
  return transitions

marketPhaseTransitions = loadMarketPhases()

def main():
  print( marketPhaseTransitions )

if __name__ == "__main__":
  main()
