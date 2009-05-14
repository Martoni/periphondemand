---------------------------------------------------------------------------
-- Company     : Vim Inc
-- Author(s)   : Fabien Marteau
-- 
-- Creation Date : 19/10/2008
-- File          : xilinx_one_port_ram_async.vhd
--
-- Abstract : Xilinx behavioural template for ram 
--
---------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.numeric_std.all;

---------------------------------------------------------------------------
Entity xilinx_one_port_ram_async is 
  ---------------------------------------------------------------------------
  generic
  (
    ADDR_WIDTH : integer := 10;
    DATA_WIDTH : integer := 16
    );
  port 
  (
    clk : in std_logic;
    we  : in std_logic ;
    addr : in std_logic_vector( ADDR_WIDTH - 1 downto 0);
    din  : in std_logic_vector( DATA_WIDTH - 1 downto 0);
    dout : out std_logic_vector( DATA_WIDTH - 1 downto 0)
    );
end entity;

---------------------------------------------------------------------------
Architecture xilinx_one_port_ram_async_1 of xilinx_one_port_ram_async is
  ---------------------------------------------------------------------------
  type ram_type is array (2**ADDR_WIDTH-1 downto 0) 
    of std_logic_vector( DATA_WIDTH-1 downto 0);
  signal ram: ram_type;
  signal addr_reg : std_logic_vector( ADDR_WIDTH-1 downto 0);
begin

  process (clk)
  begin
    if (clk'event and clk = '1') then
      if (we='1') then
        ram(to_integer(unsigned(addr)))<= din;
      end if;
      addr_reg <=  addr;
    end if;
  end process;
  dout <=  ram(to_integer(unsigned(addr_reg)));

end architecture xilinx_one_port_ram_async_1;

