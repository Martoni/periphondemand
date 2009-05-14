---------------------------------------------------------------------------
-- Company     : ARMadeus Systems
-- Author(s)   : Fabien Marteau
-- 
-- Creation Date : 05/03/2008
-- File          : wb_syscon.vhd
--
-- Abstract : 
--
---------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.numeric_std.all;
-- for dcm simulation
Library UNISIM;
use UNISIM.vcomponents.all;


---------------------------------------------------------------------------
Entity wb_syscon is 
---------------------------------------------------------------------------
port 
(
    -- external signals
    ext_clk : in std_logic ;
    --internal signals
    gls_clk : out std_logic ;
    gls_reset : out std_logic 
);
end entity;


---------------------------------------------------------------------------
Architecture wb_syscon_1 of wb_syscon is
---------------------------------------------------------------------------

    signal dly: std_logic := '0';
    signal rst: std_logic := '0';
    signal ext_reset : std_logic;

    signal CLK0  : std_logic ;
    signal CLK180 : std_logic; -- 180 degree DCM CLK output
    signal CLK270 : std_logic; -- 270 degree DCM CLK output
    signal CLK2X : std_logic;   -- 2X DCM CLK output
    signal CLK2X180 : std_logic; -- 2X, 180 degree DCM CLK out
    signal CLK90 : std_logic;   -- 90 degree DCM CLK output
    signal CLKDV : std_logic;   -- Divided DCM CLK out (CLKDV_DIVIDE)
    signal CLKFX : std_logic;   -- DCM CLK synthesis out (M/D)
    signal CLKFX180 : std_logic; -- 180 degree CLK synthesis out
    signal LOCKED : std_logic; -- DCM LOCK status output
    signal PSDONE : std_logic; -- Dynamic phase adjust done output
    signal STATUS : std_logic_vector( 7 downto 0); -- 8-bit DCM status bits output
    signal CLKFB : std_logic;   -- DCM clock feedback
    signal CLKIN : std_logic;   -- Clock input (from IBUFG, BUFG or DCM)
    signal PSCLK : std_logic;   -- Dynamic phase adjust clock input
    signal PSEN : std_logic;     -- Dynamic phase adjust enable input
    signal PSINCDEC : std_logic; -- Dynamic phase adjust increment/decrement
    --signal RST : std_logic ;        -- DCM asynchronous reset input


begin

    ext_reset <= '0';
----------------------------------------------------------------------------
--  RESET signal generator.
----------------------------------------------------------------------------
process(ext_clk)
begin
  if(rising_edge(ext_clk)) then
    dly <= ( not(ext_reset) and     dly  and not(rst) )
        or ( not(ext_reset) and not(dly) and     rst  );

    rst <= ( not(ext_reset) and not(dly) and not(rst) );
  end if;
end process;

   gls_clk <= CLK2X;
   gls_reset <= rst;
   CLKIN <= ext_clk;
   CLKFB <= CLK2X;

   -- DCM: Digital Clock Manager Circuit
   -- Virtex-II/II-Pro and Spartan-3
   -- Xilinx HDL Language Template, version 10.1

   DCM_inst : DCM
   generic map (
      CLKDV_DIVIDE => 16.0, --  Divide by: 1.5,2.0,2.5,3.0,3.5,4.0,4.5,5.0,5.5,6.0,6.5
                           --     7.0,7.5,8.0,9.0,10.0,11.0,12.0,13.0,14.0,15.0 or 16.0
      CLKFX_DIVIDE => 1,   --  Can be any interger from 1 to 32
      CLKFX_MULTIPLY => 4, --  Can be any integer from 1 to 32
      CLKIN_DIVIDE_BY_2 => FALSE, --  TRUE/FALSE to enable CLKIN divide by two feature
      CLKIN_PERIOD => 0.0,          --  Specify period of input clock
      CLKOUT_PHASE_SHIFT => "NONE", --  Specify phase shift of NONE, FIXED or VARIABLE
      CLK_FEEDBACK => "1X",         --  Specify clock feedback of NONE, 1X or 2X
      DESKEW_ADJUST => "SYSTEM_SYNCHRONOUS", --  SOURCE_SYNCHRONOUS, SYSTEM_SYNCHRONOUS or
                                             --     an integer from 0 to 15
      DFS_FREQUENCY_MODE => "LOW",     --  HIGH or LOW frequency mode for frequency synthesis
      DLL_FREQUENCY_MODE => "LOW",     --  HIGH or LOW frequency mode for DLL
      DUTY_CYCLE_CORRECTION => TRUE, --  Duty cycle correction, TRUE or FALSE
      FACTORY_JF => X"C080",          --  FACTORY JF Values
      PHASE_SHIFT => 0,        --  Amount of fixed phase shift from -255 to 255
      STARTUP_WAIT => FALSE) --  Delay configuration DONE until DCM LOCK, TRUE/FALSE
   port map (
      CLK0 =>     CLK0,     -- 0 degree DCM CLK ouptput
      CLK180 =>   CLK180, -- 180 degree DCM CLK output
      CLK270 =>   CLK270, -- 270 degree DCM CLK output
      CLK2X =>    CLK2X,   -- 2X DCM CLK output
      CLK2X180 => CLK2X180, -- 2X, 180 degree DCM CLK out
      CLK90 =>    CLK90,   -- 90 degree DCM CLK output
      CLKDV =>    CLKDV,   -- Divided DCM CLK out (CLKDV_DIVIDE)
      CLKFX =>    CLKFX,   -- DCM CLK synthesis out (M/D)
      CLKFX180 => CLKFX180, -- 180 degree CLK synthesis out
      LOCKED =>   LOCKED, -- DCM LOCK status output
      PSDONE =>   PSDONE, -- Dynamic phase adjust done output
      STATUS =>   STATUS, -- 8-bit DCM status bits output
      CLKFB =>    CLKFB,   -- DCM clock feedback
      CLKIN =>    CLKIN,   -- Clock input (from IBUFG, BUFG or DCM)
      PSCLK =>    PSCLK,   -- Dynamic phase adjust clock input
      PSEN =>     PSEN,     -- Dynamic phase adjust enable input
      PSINCDEC => PSINCDEC, -- Dynamic phase adjust increment/decrement
      RST =>      rst        -- DCM asynchronous reset input
   );

   -- End of DCM_inst instantiation





end architecture wb_syscon_1;

