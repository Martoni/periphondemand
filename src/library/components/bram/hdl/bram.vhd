---------------------------------------------------------------------------
-- Company     : Vim Inc
-- Author(s)   : Fabien Marteau
--
-- Creation Date : 14/11/2008
-- File          : bram.vhd
--
-- Abstract :
--
---------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.numeric_std.all;

---------------------------------------------------------------------------
Entity bram is
  ---------------------------------------------------------------------------
  generic(
    wb_size : natural := 16 -- Data port size for wishbone
    );
  port
  (
    -- Syscon signals
    wbs_reset    : in std_logic ;
    wbs_clk      : in std_logic ;
    -- Wishbone signals
    wbs_add       : in std_logic_vector( 9 downto 0);
    wbs_writedata : in std_logic_vector( wb_size-1 downto 0);
    wbs_readdata  : out std_logic_vector( wb_size-1 downto 0);
    wbs_strobe    : in std_logic ;
    wbs_cycle     : in std_logic ;
    wbs_write     : in std_logic ;
    wbs_ack       : out std_logic
    );
end entity;

---------------------------------------------------------------------------
Architecture bram_1 of bram is
---------------------------------------------------------------------------
  component xilinx_one_port_ram_async
    generic (
      ADDR_WIDTH : integer := 10;
      DATA_WIDTH : integer := 16
      );
    port (
      clk  : in std_logic;
      we   : in std_logic ;
      addr : in std_logic_vector( ADDR_WIDTH - 1 downto 0);
      din  : in std_logic_vector( DATA_WIDTH - 1 downto 0);
      dout : out std_logic_vector( DATA_WIDTH - 1 downto 0)
      );
  end component xilinx_one_port_ram_async;

begin

  ram : xilinx_one_port_ram_async
  generic map (
    ADDR_WIDTH => 10,
    DATA_WIDTH => 16
    )
  port map (
    clk => wbs_clk,
    we   =>  wbs_write,
    addr => wbs_add,
    din  => wbs_writedata,
    dout => wbs_readdata
  );

  wbs_ack <= wbs_strobe;

end architecture bram_1;

