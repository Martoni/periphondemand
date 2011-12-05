---------------------------------------------------------------------------
-- Company     : ARMades Systems
-- Author(s)   : Fabien Marteau <fabien.marteau@armadeus.com>
--
-- Creation Date : 25/06/2008
-- File          : uart_top_vhdl.vhd
--
-- Abstract : wrapper for uar16750 from opencores to VHDL-Wishbone16 bus
--
---------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.numeric_std.all;

---------------------------------------------------------------------------
Entity uart16750 is
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
Architecture uart_top_vhdl_1 of uart16750 is
---------------------------------------------------------------------------

    component uart_16750
        port (
                 CLK      : in std_logic;                             -- Clock
                 RST      : in std_logic;                             -- Reset
                 BAUDCE   : in std_logic;                             -- Baudrate generator clock enable
                 CS       : in std_logic;                             -- Chip select
                 WR       : in std_logic;                             -- Write to UART
                 RD       : in std_logic;                             -- Read from UART
                 A        : in std_logic_vector(2 downto 0);          -- Register select
                 DIN      : in std_logic_vector(7 downto 0);          -- Data bus input
                 DOUT     : out std_logic_vector(7 downto 0);         -- Data bus output
                 DDIS     : out std_logic;                            -- Driver disable
                 INT      : out std_logic;                            -- Interrupt output
                 OUT1N    : out std_logic;                            -- Output 1
                 OUT2N    : out std_logic;                            -- Output 2
                 RCLK     : in std_logic;                             -- Receiver clock (16x baudrate)
                 BAUDOUTN : out std_logic;                            -- Baudrate generator output (16x baudrate)
                 RTSN     : out std_logic;                            -- RTS output
                 DTRN     : out std_logic;                            -- DTR output
                 CTSN     : in std_logic;                             -- CTS input
                 DSRN     : in std_logic;                             -- DSR input
                 DCDN     : in std_logic;                             -- DCD input
                 RIN      : in std_logic;                             -- RI input
                 SIN      : in std_logic;                             -- Receiver input
                 SOUT     : out std_logic                             -- Transmitter output
             );
    end component uart_16750;


    signal wb_dat_i_int : std_logic_vector( 7 downto 0);
    signal wb_dat_o_int : std_logic_vector( 7 downto 0);

    signal strobe : std_logic ;
    signal baudrateX16 : std_logic ;
    signal uart_rd_s : std_logic;

begin

    wb_dat_i_int <= wb_dat_i(7 downto 0);

    strobe <= wb_stb_i when wb_adr_i(3) = '0' else '0';

    wb_dat_o <= std_logic_vector(to_unsigned(id,wb_size))
                when wb_adr_i = "1000" and wb_stb_i = '1' and wb_we_i = '0'
                else "00000000"&wb_dat_o_int
                when wb_adr_i(3)= '0' and wb_stb_i = '1' and wb_we_i = '0'
                else (others => '0');

    uart_rd_s <= not wb_we_i;

    uart_connect : uart_16750
    port map (
        CLK      => wb_clk_i,               -- Clock
        RST      => wb_rst_i,               -- Reset
        BAUDCE   => '1',                    -- Baudrate generator clock enable
        CS       => strobe,                 -- Chip select
        WR       => wb_we_i,                -- Write to UART
        RD       => uart_rd_s,            -- Read from UART
        A        => wb_adr_i(2 downto 0),   -- Register select
        DIN      => wb_dat_i_int,   -- Data bus input
        DOUT     => wb_dat_o_int,   -- Data bus output
        DDIS     => open,                   -- Driver disable
        INT      => int_o,                  -- Interrupt output
        OUT1N    => open,                   -- Output 1
        OUT2N    => open,                   -- Output 2
        RCLK     => baudrateX16,            -- Receiver clock (16x baudrate)
        BAUDOUTN => baudrateX16,            -- Baudrate generator output (16x baudrate)
        RTSN     => rts_pad_o,   -- RTS output
        DTRN     => dtr_pad_o,   -- DTR output
        CTSN     => cts_pad_i,   -- CTS input
        DSRN     => dsr_pad_i,   -- DSR input
        DCDN     => dcd_pad_i,   -- DCD input
        RIN      => ri_pad_i,    -- RI input
        SIN      => srx_pad_i,   -- Receiver input
        SOUT     => stx_pad_o    -- Transmitter output
    );

end architecture uart_top_vhdl_1;

