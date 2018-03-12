import pika
import json

from Logger import log

from SimulationDict import LogLevel

class RpcConsumer( object ):
  def onExit( self ):
    self.ch.stop_consuming()
 
  def on_request( self, ch, method, props, body ):

    validRequestTypes = [ 'shutdown', 'change_frequency' ]
    request = json.loads( body ) 
    if ( request['type'] in validRequestTypes ):
      response = { 'status' : 'true' }
    else:
      response = { 'status' : 'false' }
      return
 
    ch.basic_publish( exchange='',
      routing_key = props.reply_to,
      properties = pika.BasicProperties( correlation_id = props.correlation_id ),
      body = json.dumps( response )
    )
    ch.basic_ack( delivery_tag = method.delivery_tag )
    
    if ( request['type'] == 'shutdown' ):
      log( "Received RPC shutdown instruction", LogLevel.INFO )
      self.onExit()
      self.stop_callback()
    if ( request['type'] == 'change_frequency'):
      log( "Received Frequency change to %s" % ( request['frequency'] ) )
      frequency = request['frequency']
      self.change_freq_callback( frequency )
    else:
      pass

  def consume( self ):
    log( "Consuming RPC" )
    self.ch.start_consuming()
  
  def __init__ (self, cfg, stop_callback, change_freq_callback ):
    self.stop_callback = stop_callback
    self.change_freq_callback = change_freq_callback
    self.conn = pika.BlockingConnection( pika.ConnectionParameters (
      host = cfg.bus['host']
    ))
    self.ch = self.conn.channel()
    self.ch.queue_declare( 'rpc' )
    self.ch.basic_consume( self.on_request, queue='rpc' )
