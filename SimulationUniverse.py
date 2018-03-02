#!/usr/bin/python

import csv
from decimal import Decimal
from SimulationDict import *
from Markets import *
from Logger import log
from FeedMessages import *
import numpy as np


def getMinimumTickSize( currentPrice, tickSizeRange ):
  # Normally different markets have different minimum tick sizes.
  # Moreover, on many markets the tick size varies depending on the current price.
  # For now, we will assume 1 cent for all securities but the hook is here to improve this.
  if (tickSizeRange == 2):
    return Decimal('10')
  return Decimal('0.01')


def positiveIntOrDefault( val, default ):
  try:
    if int( val ) > 0:
      return int( val )
  except:
    pass
  return default

def positiveDecOrDefault( val, default ):
  try:
    if Decimal( val ) > 0:
      return Decimal( val )
  except:
    pass
  return default 


def getSecurityUniverse( securityMasterFilePath = 'SecurityMaster.dat' ):
  universe={}

  secmaster = csv.DictReader( open( securityMasterFilePath) )

  defaultValues = { 'bullishBias' : 0.50, 'quoteChangeProbability' : 0.5, 'tradeProbability' : 0.15,
    'initBid' : Decimal('10.00'), 'typicalTradeSize' : 1000, 'boardLotSize' : 1,
    'boardLotDistributionForTrades' : 100, 'typicalAggregateOrderSize' : 2500,
    'boardLotDistributionForOrders' : 500 }

  requiredHeaders = ['ticker', 'tickSizeRange', 'market', 'bullishBias', 'quoteChangeProbability',
    'tradeProbability', 'initBid', 'typicalTradeSize', 'boardLotSize', 'boardLotDistributionForTrades', 
    'typicalAggregateOrderSize', 'boardLotDistributionForOrders' ]

  for row in secmaster:
    args=[]
    for key in [ 'bullishBias', 'quoteChangeProbability', 'tradeProbability', 'initBid' ]:
      row[key] = positiveDecOrDefault( row[key], defaultValues[key] )
    for key in [ 'typicalTradeSize', 'boardLotSize', 'boardLotDistributionForTrades',
      'typicalAggregateOrderSize', 'boardLotDistributionForOrders' ]:
      row[key] = positiveIntOrDefault( row[key], defaultValues[key] )
    # convert MIC to Enum type
    row['market'] = Markets[ row['market'] ]
    for key in requiredHeaders:
      args.append( row[key] ) 
    universe[ row['ticker'] ] = Security( *args )

  return universe


class Security( object ):
  def __repr__( self ):
    return "%s: market:%s, bid: %s, ask: %s" % ( self.ticker, self.market, self.bid, self.ask )

  def __init__( self, ticker, tickSizeRange, market, bullishBias=0.50, quoteChangeProbability=0.50, tradeProbability=0.15, initBid=Decimal('10.00'), typicalTradeSize=1000, boardLotSize=1, boardLotDistributionForTrades=100, typicalAggregateOrderSize=2500, boardLotDistributionForOrders=500  ):
    self.ticker=ticker
    self.tickSizeRange=tickSizeRange
    self.market=market
    self.bullishBias=bullishBias
    self.quoteChangeProbability=quoteChangeProbability
    self.tradeProbability=tradeProbability
    self.bid = initBid
    self.ask = initBid + getMinimumTickSize( initBid, tickSizeRange )
    self.typicalTradeSize=typicalTradeSize
    self.typicalAggregateOrderSize=typicalAggregateOrderSize
    self.boardLotSize=boardLotSize
    self.boardLotDistributionForTrades=boardLotDistributionForTrades
    self.boardLotDistributionForOrders=boardLotDistributionForOrders
    self.bidSize = self.getAggregateOrderSize()
    self.askSize = self.getAggregateOrderSize()
    self.haltIndicator=HaltIndicator.NONE

  # Generate a new starting quote line, having moved one tick in the appropriate direction
  def getNextQuoteLine( self, direction ):
    if ( direction == Direction.DOWN ):
      # Do not less prices fall below the minimum tick size
      if ( self.bid > getMinimumTickSize( self.bid, self.tickSizeRange ) ):
        self.bid = self.bid - getMinimumTickSize( self.bid, self.tickSizeRange ) 
        self.ask = self.ask - getMinimumTickSize( self.ask, self.tickSizeRange ) 
    else:
      self.bid = self.bid + getMinimumTickSize( self.bid, self.tickSizeRange ) 
      self.ask = self.ask + getMinimumTickSize( self.ask, self.tickSizeRange ) 
    self.bidSize = self.getAggregateOrderSize()
    self.askSize = self.getAggregateOrderSize()

  # Generate the next trade - decrement the appropriate sharecount if possible.
  # If this calls for more shares than are available, generate a new quote line,
  # moving in the same direction as the spread was crossed.
  def getNextExecutedTrade( self, direction ):
    emptyOrderBookSide = False
    tradeVolume = self.getTradeSize()
    if (direction == Direction.DOWN):
      tradePrice = self.bid
      if ( tradeVolume > self.bidSize ):
        # Cleared out the book on this side - need to generate a new quote line.
        emptyOrderBookSide = True
      else:
        # Reduce the available shares on this side of the book.
        self.bidSize = self.bidSize - tradeVolume
    else:
      tradePrice = self.ask
      if ( tradeVolume > self.askSize ):
        # Cleared out the book on this side - need to generate a new quote line.
        emptyOrderBookSide = True
      else:
        # Reduce the available shares on this side of the book.
        self.askSize = self.askSize - tradeVolume
    log( "trading %s at $%s for %s shares" % ( self.ticker, tradePrice, tradeVolume), LogLevel.DEBUG )
    return ( tradeVolume, tradePrice, emptyOrderBookSide )
   
  def checkHaltIndicator( self ):
    # Manage security halt / IA / normal states.
    if ( self.haltIndicator == HaltIndicator.NONE ):
      if ( random() <= self.haltIndicator.value.probability ):
        self.haltIndicator = HaltIndicator.HALTED
        print( "Halted %s" % ( self.ticker ) )
    elif ( self.haltIndicator == HaltIndicator.HALTED ):
      if ( random() <= self.haltIndicator.value.probability ):
        self.haltIndicator = HaltIndicator.INTRADAY_AUCTION
        print( "Intraday Auction for %s" % ( self.ticker ) )
    elif ( self.haltIndicator == HaltIndicator.INTRADAY_AUCTION ):
      if ( random() <= self.haltIndicator.value.probability ):
        self.haltIndicator = HaltIndicator.NONE
        print( "Normal trading for %s" % ( self.ticker ) )

  def getAuctionTrade( self, direction ):
    # TODO: auction prints should be much larger than regular trade prints.
    return self.getNextExecutedTrade( direction )

  def getCurrentQuoteJson( self ):
    log( "quoting %s at $%s x %s / $%s x %s" % ( self.ticker, self.bid, self.bidSize, self.ask, self.askSize ), LogLevel.DEBUG )
    return createJsonQuoteMessage( self.ticker, self.market.value.mic, str( self.bid ), self.bidSize, str( self.ask ), self.askSize ) 

      
  def getTradeSize( self ):
    # mutate the typical trade size by a normally distributed multiple of the board lot.
    boardLotsFromTTS = np.random.randint(-1 * self.boardLotDistributionForTrades, self.boardLotDistributionForTrades)
    return self.typicalTradeSize + boardLotsFromTTS * self.boardLotSize


  def getAggregateOrderSize( self ):
    boardLotsFromAOS = np.random.randint(-1 * self.boardLotDistributionForOrders, self.boardLotDistributionForOrders)
    return self.typicalAggregateOrderSize + boardLotsFromAOS * self.boardLotSize

def main():
  return getSecurityUniverse()

if __name__ == "__main__":
  main()
