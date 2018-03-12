#!/usr/bin/python

from configparser import ConfigParser
from decimal import getcontext
from random import seed
import signal

from Simulation import Simulation
from SimulationDict import LogLevel
from SimulationPublisher import messagePublisher
from SimulationUniverse import getSecurityUniverse
from SimulationRpc import RpcConsumer
from Logger import log


seed( None )

getcontext().prec=6

class Configuration( object ):
  bus = {}
  universe = {}

  def __init__( self ):
    self.bus['host'] = 'localhost'
    self.bus['port'] = '5672'
    self.bus['vhost'] = '/'
    self.bus['user'] = 'guest'
    self.bus['password'] = 'guest'
    self.bus['exchange'] = 'rt_feeds'
    self.universe['universe_file'] = 'SecurityMaster.dat'

  def processConfigurationFile( self, fp ):
    cfg = ConfigParser() 
    cfg.readfp( fp )
   
    for section, member in [ ('bus_configuration', self.bus ), ('universe', self.universe ) ]:
      for opt in cfg.options( section ):
        if opt not in member.keys():
          log( 'Unrecognized configuration option %s in section %s' % ( opt, section ), LogLevel.WARNING )
        else:
          optval = cfg.get( section, opt )
          member[ opt ] = optval
          log( 'Setting %s.%s=%s' % ( section, opt, optval ), LogLevel.DEBUG )

def getMinimumTickSize( currentPrice, tickSizeRange ):
  # Normally different markets have different minimum tick sizes.
  # Moreover, on many markets the tick size varies depending on the current price.
  # For now, we will assume 1 cent for all securities but the hook is here to improve this.
  if (tickSizeRange == 2):
    return Decimal('10')
  return Decimal('0.01') 

class Main( object ):
  def onExit( self, signum=None, frame=None ):
    log( "Shutting down simulation", LogLevel.INFO )
    self.simulation.stop()
    self.simulation.join()
    log( "Simulation ended", LogLevel.INFO )
    log( "Shutting down message bus connection", LogLevel.INFO )
    self.rpc_consumer.onExit()
    self.message_publisher.shutdown()
  
  def __init__( self ):
    pass

 
  def main( self ):
    configurationFile='MarketFeedSimulator.cfg'
    try:
      fp = open( configurationFile, 'r' )
      log( "Processing configuration file %s" % ( configurationFile ) )
    except:
      log( "Failed to open configuration file %s" % ( configurationFile ) )
      log( "Aborting!" )
      exit(1)
    cfg = Configuration()
    cfg.processConfigurationFile( fp )

    log( "Starting feed simulation", LogLevel.INFO )
    securityUniverse = getSecurityUniverse( securityMasterFilePath = cfg.universe['universe_file'] )
    log( "Loaded Universe of %d securities" % ( len( securityUniverse )  ), LogLevel.INFO)

    self.message_publisher = messagePublisher( cfg )
    self.simulation = Simulation( securityUniverse, self.message_publisher )
    signal.signal( signal.SIGINT, self.onExit )
  
    log( "Simulation starting", LogLevel.INFO )
    self.simulation.start()
    self.rpc_consumer = RpcConsumer( cfg,
      stop_callback=self.onExit,
      change_freq_callback=self.simulation.changeFrequency
    );
    self.rpc_consumer.consume()
     

if __name__ == "__main__":
  m = Main()
  m.main()
