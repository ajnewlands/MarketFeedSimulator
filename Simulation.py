#!/usr/bin/python

from threading import Thread
from time import sleep
from random import random
from SimulationDict import *
from SimulationMarkets import Markets, MarketPhases

class Simulation( Thread ):
  eventFrequencyMs = 10
  runnable = True
 
  def stop( self ):
    self.runnable = False
 
  def __init__( self, securityUniverse, message_publisher ):
    Thread.__init__( self )
    self.securityUniverse = securityUniverse
    self.message_publisher = message_publisher

  def run( self ):
    while( self.runnable ):
      for market in Markets:                                                                                                      
        market.value.checkMarketPhase()                                                                                           
      for security in self.securityUniverse.values():                                                                                  
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
            self.message_publisher.sendMessage( 
              "%s.%s" % ( 'Equity', security.market.value.mic ),
              security.getCurrentQuoteJson()
            )
  
        if ( quotingAllowed and ( emptyOrderBookSide or random() <= security.quoteChangeProbability ) ):    
          security.getNextQuoteLine( direction )                                                            
          self.message_publisher.sendMessage( 
            "%s.%s" % ( 'Equity', security.market.value.mic ),
            security.getCurrentQuoteJson()
          )
      sleep( self.eventFrequencyMs / 1000 )                                                                      
