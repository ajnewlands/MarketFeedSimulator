#!/usr/bin/python

from configparser import ConfigParser
from decimal import getcontext
from random import seed
import signal

from Simulation import Simulation
from SimulationDict import LogLevel
from SimulationPublisher import messagePublisher
from SimulationUniverse import getSecurityUniverse
from Logger import log

seed( None )

getcontext().prec=6

class Configuration( object ):
  bus_configuration = {}

  def __init__( self ):
    self.bus_configuration['host'] = 'localhost'
    self.bus_configuration['port'] = '5672'
    self.bus_configuration['vhost'] = '/'
    self.bus_configuration['user'] = 'guest'
    self.bus_configuration['password'] = 'guest'
    self.bus_configuration['exchange'] = 'rt_feeds'

  def processConfigurationFile( self, fp ):
    cfg = ConfigParser() 
    cfg.readfp( fp )
   
    for opt in cfg.options( 'bus_configuration' ):
      if opt not in self.bus_configuration.keys():
        log( 'Unrecognized configuration option %s in section %s' % ( opt, 'bus_configuration' ), LogLevel.WARNING )
      else:
        optval = cfg.get( 'bus_configuration', opt )
        self.bus_configuration[ opt ] = optval
        log( 'Setting %s.%s=%s' % ( 'bus_configuration', opt, optval ), LogLevel.DEBUG )

def getMinimumTickSize( currentPrice, tickSizeRange ):
  # Normally different markets have different minimum tick sizes.
  # Moreover, on many markets the tick size varies depending on the current price.
  # For now, we will assume 1 cent for all securities but the hook is here to improve this.
  if (tickSizeRange == 2):
    return Decimal('10')
  return Decimal('0.01') 

def getOldSecurityUniverse( securityMasterFilePath=None ):
  # For now we will use a hard coded security universe, but in the long run we would use a universe file.
  securityUniverse={}
  securityUniverse['7974'] = Security( ticker='7974', tickSizeRange=2, market=Markets.XTKS, initBid=Decimal('46400') )
  securityUniverse['BHP'] = Security( ticker='BHP', tickSizeRange=1, market=Markets.XASX, initBid=Decimal('30.68') )
  #securityUniverse['WOW'] = Security( ticker='WOW', tickSizeRange=1, market=Markets.XASX, initBid=Decimal('26.92') )
  #securityUniverse['CBA'] = Security( ticker='CBA', tickSizeRange=1, market=Markets.XASX, initBid=Decimal('75.46') )
  #securityUniverse['AMP'] = Security( ticker='AMP', tickSizeRange=1, market=Markets.XASX, initBid=Decimal('5.25'), typicalTradeSize=500, boardLotDistributionForTrades=250, typicalAggregateOrderSize=4000, boardLotDistributionForOrders=2000  )

  return securityUniverse




class Main( object ):
  def onExit( self, signum=None, frame=None ):
    log( "Shutting down simulation", LogLevel.INFO )
    self.simulation.stop()
    log( "Shutting down message bus connection", LogLevel.INFO )
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
    securityUniverse = getSecurityUniverse( securityMasterFilePath='SecurityMaster.dat' )
    log( "Loaded Universe of %d securities" % ( len( securityUniverse )  ), LogLevel.INFO)

    self.message_publisher = messagePublisher( cfg )
    self.simulation = Simulation( securityUniverse, self.message_publisher )
    signal.signal( signal.SIGINT, self.onExit )
  
    log( "Simulation starting", LogLevel.INFO )
    self.simulation.start()
 
    self.simulation.join()
    log( "Simulation ended", LogLevel.INFO )

if __name__ == "__main__":
  m = Main()
  m.main()
