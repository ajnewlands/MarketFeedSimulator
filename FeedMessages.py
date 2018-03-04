#!/usr/bin/python

from enum import Enum
from SimulationDict import HaltIndicator
import json

class messageType( Enum ):
  quote='Q'
  trade='T'
  marketStatus='M'

def createJsonTradeMessage( security ):
  msg = {}
  msg [ 't' ] = messageType.trade.value
  msg[ 'sym' ] = security.ticker
  msg[ 'ex' ] = security.market.value.mic
  msg[ 'p' ] = str( security.lastPrice )
  msg[ 's' ] = security.lastSize

  return json.dumps( msg )
  

def createJsonMarketStatusMessage( market ):
  msg = {}
  msg[ 't' ] = messageType.marketStatus.value
  msg[ 'ex' ] = market.mic
  msg[ 'st' ] = market.currentPhase.name
  
  return json.dumps( msg )

#def createJsonQuoteMessage( ticker, exchange, bid, bidsz, ask, asksz, qcond=1 ):
def createJsonQuoteMessage( security, qcond=1 ):
  msg = {}
  if (security.haltIndicator == HaltIndicator.HALTED ): 
    hi = 1
  else:
    hi = 0
  
  if (security.haltIndicator == HaltIndicator.INTRADAY_AUCTION ):
    ia = 1
  else:
    ia = 0

  msg[ 't' ] = messageType.quote.value
  msg[ 'sym' ] = security.ticker
  msg[ 'ex' ] = security.market.value.mic
  msg[ 'b' ] = str( security.bid )
  msg[ 'bs' ] = security.bidSize
  msg[ 'a' ] = str( security.ask )
  msg[ 'as' ] = security.askSize
  msg[ 'hi'] = hi 
  msg[ 'ia' ] = ia
  msg[ 'qc' ] = qcond

  return json.dumps( msg )

