from enum import Enum, IntEnum

# Directionality for price movement    
class Direction( Enum ):
  UP=1
  DOWN=2
                                       
class LogLevel( IntEnum ):
  DEBUG=1
  INFO=2
  WARNING=3
  CRITICAL=4

class HaltStates( object ):	
  def __init__ (self, probability, tradingAllowed=False, quotingAllowed=False):
    self.probability=probability
    self.tradingAllowed=tradingAllowed
    self.quotingAllowed=quotingAllowed

class HaltIndicator( Enum ):
  NONE=HaltStates( 0.01, tradingAllowed=True, quotingAllowed=True )
  HALTED=HaltStates( 0.1 )
  INTRADAY_AUCTION=HaltStates( 0.1, tradingAllowed=False, quotingAllowed=True )
