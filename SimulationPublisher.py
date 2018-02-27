#!/usr/bin/python

import pika
import json

class messagePublisher( object ):
  def __init__( self, message_bus_exchange='rt_feeds' ):
    self.connection= pika.BlockingConnection( pika.ConnectionParameters( host='localhost' ) )
    self.channel = self.connection.channel()
    self.channel.exchange_declare(exchange=message_bus_exchange,
                         exchange_type='topic')
    self.exchange = message_bus_exchange
    message= json.dumps( { 'ticker' : 'BHP', 'mic' : 'XASX' } )

  def sendMessage( self, routing_key, msg ):
    self.channel.basic_publish(exchange=self.exchange,
      routing_key=routing_key,
      body=msg)
    print(" [x] Sent %r:%r" % (routing_key, msg))

  def shutdown( self ):
    self.connection.close()

def main():
  bus = messagePublisher( 'rt_feeds' )
  bus.sendMessage(  json.dumps( { 'ticker' : 'BHP', 'mic' : 'XASX' } ) )
  bus.shutdown()

if __name__ == "__main__":
  main()
