---------------------------------------------------------------------------
-- Company     : ARMades Systems
-- Author(s)   : Fabien Marteau <fabien.marteau@armadeus.com>
--
-- Creation Date : 03/09/2008
-- File          : simplegpio.vhd
--
-- Abstract :
--
---------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.numeric_std.all;

---------------------------------------------------------------------------
Entity simplegpio is
---------------------------------------------------------------------------
generic(
    id : natural := 3;   -- identify id
    size : natural := 16 -- wishbone data size 8,16 or 32
);
port
(
    -- clock and reset
	clk_i : in std_logic ; -- master clock input
	rst_i : in std_logic ; -- asynchronous reset

    -- wishbone
	adr_i : in std_logic_vector( 1 downto 0);
	dat_i : in std_logic_vector( size-1 downto 0);
	dat_o : out std_logic_vector( size-1 downto 0);
	we_i  : in std_logic ;
	stb_i : in std_logic ;
	ack_o : out std_logic ;
    cyc_i : in std_logic;

    -- gpio
    gpio : inout std_logic_vector( size-1 downto 0)

);
end entity;


---------------------------------------------------------------------------
Architecture simplegpio_1 of simplegpio is
---------------------------------------------------------------------------

    signal write_register : std_logic_vector( size-1 downto 0);
    signal ctrl_register  : std_logic_vector( size-1 downto 0);

    signal rd_ack : std_logic ;
    signal wr_ack : std_logic ;
begin

-- register reading process
process(clk_i, rst_i)
begin
  if(rst_i = '1') then
    dat_o    <= (others => '0');
    rd_ack <= '0';
  elsif(rising_edge(clk_i)) then
    rd_ack  <= '0';

    if(stb_i = '1' and we_i = '0' and cyc_i = '1') then
      rd_ack  <= '1';
      if(adr_i = "00") then
        dat_o <= gpio;
      elsif(adr_i = "01") then
        dat_o <= ctrl_register;
      elsif(adr_i = "10") then
        dat_o <= std_logic_vector(to_unsigned(id,size));
      else
        dat_o <= (others => '0');
      end if;
    end if;
  end if;
end process;

-- register write process
process(clk_i,rst_i)
begin
    if(rst_i = '1') then
        ctrl_register <= (others => '0');
        write_register <= (others => '0');
        wr_ack <= '0';
    elsif(rising_edge(clk_i)) then
        wr_ack <= '0';
        if(stb_i = '1' and we_i = '1' and cyc_i = '1') then
            wr_ack <=  '1';
            if(adr_i = "00") then
                write_register <= dat_i;
            elsif(adr_i = "01") then
                ctrl_register  <= dat_i;
            end if;
        end if;
    end if;
end process;

-- acknowledge
ack_o <= rd_ack or wr_ack;

-- gpio write
gpiogen : for i in 0 to (size-1) generate
    gpio(i) <= write_register(i) when ctrl_register(i) = '1' else 'Z';
end generate;

end architecture simplegpio_1;

