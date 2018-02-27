#!/usr/bin/python

from enum import Enum
import json

class messageType( Enum ):
  quote=1
  trade=2
  marketStatus=3

def createJsonQuoteMessage( ticker, exchange, bid, bidsz, ask, asksz, qcond=1 ):
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

