---------------------------------------------------------------------------
-- Company     : ARMades Systems
-- Author(s)   : Fabien Marteau <fabien.marteau@armadeus.com>
--
-- Creation Date : 25/06/2008
-- File          : uart_top_vhdl.vhd
--
-- Abstract : wrapper for uart16550 from opencores to VHDL-Wishbone16 bus
--
---------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.numeric_std.all;

---------------------------------------------------------------------------
Entity uart16550 is
---------------------------------------------------------------------------
    generic(
        id : natural := 1;
        wb_size : natural := 16
    );
    port (
    -- clock
    wb_clk_i : in std_logic;
    wb_rst_i : in  std_logic;
    -- Wishbone interface
    wb_adr_i : in  std_logic_vector( 3 downto 0);
    wb_dat_i : in  std_logic_vector( 15 downto 0);
    wb_dat_o : out std_logic_vector( 15 downto 0);
    wb_we_i  : in  std_logic ;
    wb_stb_i : in  std_logic ;
    wb_cyc_i : in  std_logic ;
    wb_ack_o : out std_logic ;
    -- interrupt
    int_o    : out std_logic ;
    -- uart signals
    srx_pad_i : in  std_logic ;
    stx_pad_o : out std_logic ;
    rts_pad_o : out std_logic ;
    cts_pad_i : in  std_logic ;
    dtr_pad_o : out std_logic ;
    dsr_pad_i : in  std_logic ;
    ri_pad_i  : in  std_logic ;
    dcd_pad_i : in  std_logic
    -- optional baudrate output
--    baud_o  : out std_logic
    );

end entity;


---------------------------------------------------------------------------
Architecture uart_top_vhdl_1 of uart16550 is
---------------------------------------------------------------------------

    component uart_top
    port (
    -- clock
    wb_clk_i : in std_logic;
    wb_rst_i : in std_logic;
    -- Wishbone interface
    wb_adr_i : in std_logic_vector( 2 downto 0);
    wb_dat_i : in std_logic_vector( 7 downto 0);
    wb_dat_o : out std_logic_vector(7 downto 0);
    wb_we_i  : in std_logic ;
    wb_stb_i : in std_logic ;
    wb_cyc_i : in std_logic ;
    wb_sel_i : in std_logic_vector( 3 downto 0);
    wb_ack_o : out std_logic ;
    int_o    : out std_logic ;
    -- uart signals
    srx_pad_i : in std_logic ;
    stx_pad_o : out std_logic ;
    rts_pad_o : out std_logic ;
    cts_pad_i : in std_logic ;
    dtr_pad_o : out std_logic ;
    dsr_pad_i : in std_logic ;
    ri_pad_i  : in std_logic ;
    dcd_pad_i : in std_logic
    -- optional baudrate output
--    baud_o  : out std_logic
    );
    end component;

    signal wb_dat_i_int : std_logic_vector( 7 downto 0);
    signal wb_dat_o_int : std_logic_vector( 7 downto 0);

    signal strobe : std_logic ;

begin

    wb_dat_i_int <= wb_dat_i(7 downto 0);

    strobe <= wb_stb_i when wb_adr_i(3) = '0' else '0';

    wb_dat_o <= std_logic_vector(to_unsigned(id,wb_size))
                when wb_adr_i = "1000" and wb_stb_i = '1' and wb_we_i = '0'
                else "00000000"&wb_dat_o_int
                when wb_adr_i(3)= '0' and wb_stb_i = '1' and wb_we_i = '0'
                else (others => '0');

    uart_connect : uart_top
    port map (
    wb_clk_i => wb_clk_i,
    wb_rst_i => wb_rst_i,
    -- Wishbone
    wb_adr_i => wb_adr_i(2 downto 0),
    wb_dat_i => wb_dat_i_int,
    wb_dat_o => wb_dat_o_int,
    wb_we_i  => wb_we_i,
    wb_stb_i => strobe,
    wb_cyc_i => wb_cyc_i,
    wb_sel_i => "0001", -- byte always on LSB
    wb_ack_o => wb_ack_o,
    int_o    => int_o,
    -- uart s
    srx_pad_i =>  srx_pad_i,
    stx_pad_o =>  stx_pad_o,
    rts_pad_o =>  rts_pad_o,
    cts_pad_i =>  cts_pad_i,
    dtr_pad_o =>  dtr_pad_o,
    dsr_pad_i =>  dsr_pad_i,
    ri_pad_i  =>  ri_pad_i,
    dcd_pad_i =>  dcd_pad_i
    -- option
--    baud_o    => baud_o
    );
	
end architecture uart_top_vhdl_1;

