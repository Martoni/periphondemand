---------------------------------------------------------------------------
-- Company     : ARMadeus Systems
-- Author(s)   : Fabien Marteau
--
-- Creation Date : 05/03/2008
-- File          : clockmeasurement.vhd
--
-- Abstract : measure clock frequency of low_clock
--
-- mapping:
-- 0x0 : Id
-- 0x1 : counter
--
-- frequency is FpgaClock/counter
--
---------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.numeric_std.all;

-----------------------------------------------------------------------
    Entity clockmeas is
-----------------------------------------------------------------------
    generic(
        id : natural := 1;
        wb_size : natural := 16 -- Data port size for wishbone
    );
    port
    (
        -- Syscon signals
        gls_reset    : in std_logic ;
        gls_clk      : in std_logic ;
        -- Wishbone signals
        wbs_add       : in std_logic ;
        wbs_writedata : in std_logic_vector( wb_size-1 downto 0);
        wbs_readdata  : out std_logic_vector( wb_size-1 downto 0);
        wbs_strobe    : in std_logic ;
        wbs_cycle      : in std_logic ;
        wbs_write     : in std_logic ;
        wbs_ack       : out std_logic;
        -- input clock signal
        low_clock : in std_logic
    );
end entity clockmeas;


-----------------------------------------------------------------------
Architecture clockmeas_1 of clockmeas is
-----------------------------------------------------------------------
    signal wb_reg : std_logic_vector( wb_size-1 downto 0);
    signal reset_counter : std_logic ;
begin

wbs_ack <= wbs_strobe;

-- read wb_register
read_bloc : process(gls_clk, gls_reset)
begin
    if gls_reset = '1' then
        wbs_readdata <= (others => '0');
    elsif rising_edge(gls_clk) then
        if (wbs_strobe = '1' and wbs_write = '0'  and wbs_cycle = '1' ) then
            if wbs_add = '0' then
                wbs_readdata <= std_logic_vector(to_unsigned(id,wb_size));
            else
                wbs_readdata <= wb_reg;
            end if;
        else
            wbs_readdata <= (others => '0');
        end if;
    end if;
end process read_bloc;

-- the counter
count : process(gls_clk,gls_reset)
    variable counter : natural range 0 to 65535;
begin
    if gls_reset = '1' then
      counter := 0;
    elsif rising_edge(gls_clk) then
      counter := counter + 1;
      if reset_counter = '1' then
        wb_reg <=std_logic_vector(to_unsigned(counter,wb_size));
        counter := 0;
      end if;
    end if;
end process count;

-- edge detection
edge : process(gls_clk,gls_reset)
  variable old_low_clock : std_logic ;
begin
  if gls_reset = '1' then
    old_low_clock := '1';
    reset_counter <= '0';
  elsif rising_edge(gls_clk) then
    if (old_low_clock = '0') and (low_clock = '1') then
      reset_counter <= '1';
    else
      reset_counter <= '0';
    end if;
    old_low_clock := low_clock;
  end if;
end process edge;

end architecture clockmeas_1;

