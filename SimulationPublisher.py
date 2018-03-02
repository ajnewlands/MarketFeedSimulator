#!/usr/bin/python

import pika
import json
import sys

class messagePublisher( object ):
  def __init__( self, cfg ):
    creds = pika.PlainCredentials( cfg.bus['user'], cfg.bus['password'] )
    self.connection= pika.BlockingConnection( pika.ConnectionParameters( 
      host = cfg.bus['host'],
      port = cfg.bus['port'],
      virtual_host = cfg.bus['vhost'],
      credentials = creds  ) )
    self.channel = self.connection.channel()
    self.channel.exchange_declare(exchange=cfg.bus['exchange'],
                         exchange_type='topic')
    self.exchange = cfg.bus['exchange']
    message= json.dumps( { 'ticker' : 'BHP', 'mic' : 'XASX' } )

  def sendMessage( self, routing_key, msg ):
    try:
      self.channel.basic_publish(exchange=self.exchange,
        routing_key=routing_key,
        body=msg)
      #print(" [x] Sent %r:%r" % (routing_key, msg))
    except pika.exceptions.ConnectionClosed:
      print(" THIS SHOULD BE A LOG MESSAGE - connection closed!" )      
      sys.exit( 1 )
      

  def shutdown( self ):
    self.connection.close()

def main():
  bus = messagePublisher( 'rt_feeds' )
  bus.sendMessage(  json.dumps( { 'ticker' : 'BHP', 'mic' : 'XASX' } ) )
  bus.shutdown()

if __name__ == "__main__":
  main()
