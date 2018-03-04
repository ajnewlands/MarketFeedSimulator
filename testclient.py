#!/usr/bin/env python
import pika
import sys
import json
import signal

from FeedMessages import *
from SimulationMarketPhases import MarketPhases

def printTradeMessage( parsed_message ):
  ticker = parsed_message[ 'sym' ]
  exchange = parsed_message[ 'ex' ]
  price = parsed_message[ 'p' ]
  size = parsed_message[ 's' ]
  trade_condition = tradeCondition( parsed_message[ 'tc' ] ).name

  print( "T|TICKER=%s|EXCHANGE=%s|LASTPRICE=%s|LASTSIZE=%s|TCOND=%s" % ( ticker, exchange, price, size, trade_condition ) )

def printQuoteMessage( parsed_message ):
  ticker = parsed_message[ 'sym' ]
  exchange = parsed_message[ 'ex' ]
  bid = parsed_message[ 'b' ]
  bid_size = parsed_message[ 'bs' ]
  bid_cond = quoteCondition( parsed_message[ 'bc' ] ).name
  ask = parsed_message[ 'a' ]
  ask_size = parsed_message[ 'as' ]
  ask_cond = quoteCondition( parsed_message[ 'ac' ] ).name
  halt_status_indicator = parsed_message[ 'hi' ]
  intraday_auction_indicator = parsed_message[ 'ia' ]

  print( "Q|TICKER=%s|EXCHANGE=%s|BID=%s|BIDSIZE=%s|ASK=%s|ASKSIZE=%s|QCOND=%s,%s|HALT=%s|IA=%s" % ( ticker, exchange, bid, bid_size,
    ask, ask_size, bid_cond, ask_cond, halt_status_indicator, intraday_auction_indicator )
  )

def printStatusMessage( parsed_message ):
  exchange = parsed_message[ 'ex' ]
  session_type = MarketPhases[ parsed_message[ 'st' ] ].value.description
  
  print( "S|EXCHANGE=%s|PHASE=%s" % ( exchange, session_type ) )

def callback(ch, method, properties, body):
  parsed_message = json.loads( body )
  message_type = messageType( parsed_message['t'] )
  if message_type == messageType.quote:
    printQuoteMessage( parsed_message ) 
  if message_type == messageType.marketStatus:
    printStatusMessage( parsed_message )
  if message_type == messageType.trade:
    printTradeMessage( parsed_message )

def onExit( sigNum=None, frame=None ):
  print( "Exiting" )
  sys.exit(0)

def main():
  signal.signal( signal.SIGINT, onExit )
  connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
  channel = connection.channel()

  channel.exchange_declare(exchange='rt_feeds',
    exchange_type='topic'
  )

  result = channel.queue_declare(exclusive=True)
  queue_name = result.method.queue

  binding_keys = sys.argv[1:]
  if not binding_keys:
    sys.stderr.write("Usage: %s [binding_key]...\n" % sys.argv[0])
    sys.exit(1)

  for binding_key in binding_keys:
    channel.queue_bind(exchange='rt_feeds',
      queue=queue_name,
      routing_key=binding_key
    )

  channel.basic_consume(callback,
    queue=queue_name,
    no_ack=True
  )

  channel.start_consuming()



if __name__ == "__main__":
  main()
