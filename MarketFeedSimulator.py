#!/usr/bin/python

from decimal import Decimal, getcontext
from time import sleep
from random import random, seed
from enum import Enum, IntEnum 
from sys import exit
import signal
import numpy as np
import json

from Markets import *
from SimulationPublisher import messagePublisher

eventFrequencyMs=10
seed( None )

getcontext().prec=6

message_publisher = messagePublisher( 'rt_feeds' )

class messageType( Enum ):
  quote=1
  trade=2
  marketStatus=3

def getQuoteMessage( ticker, exchange, bid, bidsz, ask, asksz, qcond=1 ):
  msg = {}
  msg[ 'type' ] = messageType.quote.value
  msg[ 'ticker' ] = ticker
  msg[ 'exchange' ] = exchange
  msg[ 'bid' ] = bid
  msg[ 'bidsz' ] = bidsz
  msg[ 'ask' ] = ask
  msg[ 'asksz' ] = asksz
  msg[ 'qcond' ] = qcond
  return json.dumps( msg )

# Directionality for price movement
class Direction( Enum ):
  UP=1
  DOWN=2

class LogLevel( IntEnum ):
  DEBUG=1
  INFO=2 
  WARNING=3
  CRITICAL=4

def publish( assetClass, exchange, message ):
  message_publisher.sendMessage( "%s.%s" % ( assetClass, exchange ), message )

def log( message, level=LogLevel.DEBUG, flush=False ):
  if ( level >= LogLevel.DEBUG ):
    print( message, flush=flush )

class HaltStates( object ):
  def __init__ (self, probability, tradingAllowed=False, quotingAllowed=False):
    self.probability=probability
    self.tradingAllowed=tradingAllowed
    self.quotingAllowed=quotingAllowed

class HaltIndicator( Enum ):
  NONE=HaltStates( 0.01, tradingAllowed=True, quotingAllowed=True )
  HALTED=HaltStates( 0.1 )
  INTRADAY_AUCTION=HaltStates( 0.1, tradingAllowed=False, quotingAllowed=True )

class Security( object ):
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
    self.bidSize = getAggregateOrderSize( self )
    self.askSize = getAggregateOrderSize( self )
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
    self.bidSize = getAggregateOrderSize( self )
    self.askSize = getAggregateOrderSize( self )

  # Generate the next trade - decrement the appropriate sharecount if possible.
  # If this calls for more shares than are available, generate a new quote line,
  # moving in the same direction as the spread was crossed.
  def getNextExecutedTrade( self, direction ):
    emptyOrderBookSide = False
    tradeVolume = getTradeSize( self )
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

  def logCurrentQuote( self ):
    #etQuoteMessage( ticker, exchange, bid, bidsz, ask, asksz, qcond=1 ):
    log( "quoting %s at $%s x %s / $%s x %s" % ( self.ticker, self.bid, self.bidSize, self.ask, self.askSize ), LogLevel.DEBUG )
    publish( assetClass='Equity',
      exchange = self.market.value.mic,
      message = getQuoteMessage( self.ticker, self.market.value.mic, str( self.bid ), self.bidSize, str( self.ask ), self.askSize )
    )
      
def getTradeSize( security ):
  # mutate the typical trade size by a normally distributed multiple of the board lot.
  boardLotsFromTTS = np.random.randint(-1 * security.boardLotDistributionForTrades, security.boardLotDistributionForTrades)
  return security.typicalTradeSize + boardLotsFromTTS * security.boardLotSize

def getAggregateOrderSize( security ):
  boardLotsFromAOS = np.random.randint(-1 * security.boardLotDistributionForOrders, security.boardLotDistributionForOrders)
  return security.typicalAggregateOrderSize + boardLotsFromAOS * security.boardLotSize
 
def getMinimumTickSize( currentPrice, tickSizeRange ):
  # Normally different markets have different minimum tick sizes.
  # Moreover, on many markets the tick size varies depending on the current price.
  # For now, we will assume 1 cent for all securities but the hook is here to improve this.
  if (tickSizeRange == 2):
    return Decimal('10')
  return Decimal('0.01') 

def getSecurityUniverse( securityMasterFilePath=None ):
  # For now we will use a hard coded security universe, but in the long run we would use a universe file.
  securityUniverse={}
  securityUniverse['7974'] = Security( ticker='7974', tickSizeRange=2, market=Markets.XTKS, initBid=Decimal('46400') )
  securityUniverse['BHP'] = Security( ticker='BHP', tickSizeRange=1, market=Markets.XASX, initBid=Decimal('30.68') )
  #securityUniverse['WOW'] = Security( ticker='WOW', tickSizeRange=1, market=Markets.XASX, initBid=Decimal('26.92') )
  #securityUniverse['CBA'] = Security( ticker='CBA', tickSizeRange=1, market=Markets.XASX, initBid=Decimal('75.46') )
  #securityUniverse['AMP'] = Security( ticker='AMP', tickSizeRange=1, market=Markets.XASX, initBid=Decimal('5.25'), typicalTradeSize=500, boardLotDistributionForTrades=250, typicalAggregateOrderSize=4000, boardLotDistributionForOrders=2000  )

  return securityUniverse

def runSimulationLoop( securityUniverse ):
  while( True ):
    for market in Markets:
      market.value.checkMarketPhase()
    for security in securityUniverse.values():
      # Check whether this security has moved in/out of a halted state
      if ( security.market.value.currentPhase == MarketPhases.OPEN ):
        security.checkHaltIndicator()

      # bullish bias dictates the probability of crossing the bid/ask spread in either direction.
      # bullish bias also dictates the likely direction of any quote change
      # for sake of sanity, we evaluate direction once and move both events in the same direction.
      emptyOrderBookSide=False
      tradingAllowed = security.market.value.currentPhase.value.tradingAllowed and security.haltIndicator.value.tradingAllowed
      quotingAllowed = security.market.value.currentPhase.value.quotingAllowed and security.haltIndicator.value.quotingAllowed
      auctionPrint = security.market.value.currentPhase.value.auctionPrint

      if (random() > security.bullishBias ):    
        direction = Direction.UP
      else:
        direction = Direction.DOWN 
  
      # Halted stocks won't get an auction print
      if ( auctionPrint and security.haltIndicator != HaltIndicator.HALTED ):
        tradeVolume, tradePrice, emptyOrderBookSide = security.getAuctionTrade( direction )
      if ( tradingAllowed and random() <= security.tradeProbability ):
        tradeVolume, tradePrice, emptyOrderBookSide = security.getNextExecutedTrade( direction )
        if not emptyOrderBookSide:
          security.logCurrentQuote()
      if ( quotingAllowed and ( emptyOrderBookSide or random() <= security.quoteChangeProbability ) ):
        security.getNextQuoteLine( direction )
        security.logCurrentQuote()
    sleep( eventFrequencyMs / 1000 )

def onExit( signum=None, frame=None ):
  log( "Shutting down simulation", LogLevel.INFO )
  message_publisher.shutdown()
  log( "Shutting down message publisher", LogLevel.INFO )
  exit( 0 )

def main():
  log( "Starting feed simulation", LogLevel.INFO )
  securityUniverse = getSecurityUniverse( securityMasterFilePath=None )
  log( "Loaded Universe of %d securities" % ( len( securityUniverse )  ), LogLevel.INFO)
  signal.signal( signal.SIGINT, onExit )

  runSimulationLoop( securityUniverse )

if __name__ == "__main__":
  main()
