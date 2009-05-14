---------------------------------------------------------------------------
-- Company     : ARMades Systems
-- Author(s)   : Fabien Marteau <fabien.marteau@armadeus.com>
-- 
-- Creation Date : 25/07/2008
-- File          : int_gen.vhd
--
-- Abstract : 
--
---------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.numeric_std.all;

---------------------------------------------------------------------------
Entity int_gen is 
---------------------------------------------------------------------------
generic
(
    periode : integer := 1_000_000;  -- period between two IT in microseconds
    clockperiode : integer := 10     -- clock period in nanoseconds
);
port 
(
    -- candr
    clk   : in std_logic ;
    reset : in std_logic ;
    -- wb16
    readdata    : out std_logic_vector( 15 downto 0) ; 
    writedata   : in  std_logic_vector( 15 downto 0) ;
    ack         : out std_logic ;
    strobe      : in  std_logic ;
    cycle       : in  std_logic ;
    write       : in  std_logic ;
    -- interrupts
    interrupts : out std_logic_vector( 15 downto 0) 
);
end entity;


---------------------------------------------------------------------------
Architecture int_gen_1 of int_gen is
---------------------------------------------------------------------------

    constant N : integer := ((periode)/(clockperiode))*1000; 
    signal  rd_ack : std_logic := '0';
    signal  wr_ack : std_logic := '0';
    signal  state : std_logic_vector( 15 downto 0);
    signal  count : integer range 0 to (N-1);

begin

    -- read process
    readp : process(clk,reset)
    begin
      if(reset='1') then
        rd_ack    <= '0';
        readdata  <= (others => '0');
      elsif(rising_edge(clk)) then
        rd_ack  <= '0';
        if(strobe = '1' and write = '0' and cycle = '1') then
          rd_ack  <= '1';
          readdata <= state;
        end if;
      end if;
    end process;

    -- write process
    writep : process(clk,reset)
        variable enable : std_logic := '0';
    begin
        if (reset = '1') then
            wr_ack <= '0';
            count <= 0;
            state <= (others => '0');
            enable := '0';
        elsif rising_edge(clk) then
            if(strobe = '1' and write = '1' and cycle = '1') then
                wr_ack <= '1';
                state <= writedata;
                count <= 0;
            elsif enable = '1' or wr_ack = '1' then 
                enable := '1';
                if count = (N-1) then
                    count <= 0;
                    state <= state(14 downto 0)&state(15);
                    interrupts <= state;
                else
                    count <= count + 1;
                    state <= state;
                    interrupts <= (others => '0');
                end if;
            else 
                wr_ack <= '0';
            end if;
        end if;
    end process writep;

    ack <= wr_ack or rd_ack;

	
end architecture int_gen_1;

