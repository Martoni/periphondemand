---------------------------------------------------------------------------
-- Company     : ARMadeus Systems
-- Author(s)   : Kevin JOLY joly.kevin25@gmail.com
--
-- Creation Date : 2011-05-05
-- File          : Top_sja1000_pod_tb.vhd
--
-- Abstract :
-- This testbench is used for simulate a read, a write and then, a read
-- on the SJA1000 CAN Controller interface. The read register is 0x11
-- and the written register is 0x12 in the SJA1000. The read value
-- in the SJA1000 is 0x57 simulated by the process simu_sja.
-- The written value is 0xAA.
--
---------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.numeric_std.all;

--
--                 Defines communication functions between imx and fpga:
--
--                 write procedures
--                 procedure imx_write
--                 Params :
--                 address      : Write address
--                 value        : value to write
--                 gls_clk      : clock signal
--                 imx_cs_n     : Chip select
--                 imx_oe_n     : Read signal
--                 imx_eb3_n    : Write signal
--                 imx_address  : Address signal
--                 imx_data     : Data signal
--                 WSC          : Value of imx WSC (see MC9328MXLRM.pdf p169) for sync=0
--
--                 read procedures
--                 procedure imx_read
--                 Params :
--                 address      : Write address
--                 value        : value returned
--                 gls_clk      : clock signal
--                 imx_cs_n     : Chip select
--                 imx_oe_n     : Read signal
--                 imx_eb3_n    : Write signal
--                 imx_address  : Address signal
--                 imx_data     : Data signal
--                 WSC          : Value of imx WSC (see MC9328MXLRM.pdf p169) for sync=0
--
use work.apf27_test_pkg.all;

entity top_sja1000_pod_tb is
end entity top_sja1000_pod_tb;

architecture RTL of top_sja1000_pod_tb is

    CONSTANT HALF_PERIODE : time := 5.0 ns;  -- Half clock period
    CONSTANT SJA1000_ID : std_logic_vector := x"0000";
    CONSTANT RX_ID1_REG : std_logic_vector := x"0022";
    CONSTANT RX_ID2_REG : std_logic_vector := x"0024";
    CONSTANT CLOCK_CYCLES : integer := 12;
    signal  imx27_wb16_wrapper00_imx_cs_n :  std_logic;
    signal  imx27_wb16_wrapper00_imx_data :  std_logic_vector(15 downto 0);
    signal  rstgen_syscon00_ext_clk :  std_logic;
    signal  imx27_wb16_wrapper00_imx_eb0_n :  std_logic;
    signal  imx27_wb16_wrapper00_imx_oe_n :  std_logic;
    signal  imx27_wb16_wrapper00_imx_address :  std_logic_vector(11 downto 0);
    signal  sja100000_sja_wr :  std_logic;
    signal  sja100000_sja_cs :  std_logic;
    signal  sja100000_sja_rd :  std_logic;
    signal  sja100000_sja_ale_as :  std_logic;
    signal  sja100000_sja_ad :  std_logic_vector(7 downto 0);

    component top_sja1000_pod
    port (        imx27_wb16_wrapper00_imx_cs_n : in std_logic;
        imx27_wb16_wrapper00_imx_data : inout std_logic_vector(15 downto 0);
        rstgen_syscon00_ext_clk : in std_logic;
        imx27_wb16_wrapper00_imx_eb0_n : in std_logic;
        imx27_wb16_wrapper00_imx_oe_n : in std_logic;
        imx27_wb16_wrapper00_imx_address : in std_logic_vector(11 downto 0);
        sja100000_sja_wr : out std_logic;
        sja100000_sja_cs : out std_logic;
        sja100000_sja_rd : out std_logic;
        sja100000_sja_ale_as : out std_logic;
        sja100000_sja_ad : inout std_logic_vector(7 downto 0)
    );
    end component top_sja1000_pod;
    signal value : std_logic_vector (15 downto 0);
begin

    top : top_sja1000_pod
    port map(
        imx27_wb16_wrapper00_imx_cs_n => imx27_wb16_wrapper00_imx_cs_n,
        imx27_wb16_wrapper00_imx_data => imx27_wb16_wrapper00_imx_data,
        rstgen_syscon00_ext_clk => rstgen_syscon00_ext_clk,
        imx27_wb16_wrapper00_imx_eb0_n => imx27_wb16_wrapper00_imx_eb0_n,
        imx27_wb16_wrapper00_imx_oe_n => imx27_wb16_wrapper00_imx_oe_n,
        imx27_wb16_wrapper00_imx_address => imx27_wb16_wrapper00_imx_address,
        sja100000_sja_wr => sja100000_sja_wr,
        sja100000_sja_cs => sja100000_sja_cs,
        sja100000_sja_rd => sja100000_sja_rd,
        sja100000_sja_ale_as => sja100000_sja_ale_as,
        sja100000_sja_ad => sja100000_sja_ad
    );
    stimulis : process
    begin
    -- write stimulis here
        imx27_wb16_wrapper00_imx_oe_n <= '1';
        imx27_wb16_wrapper00_imx_eb0_n <= '1';
        imx27_wb16_wrapper00_imx_cs_n <= '1';
        imx27_wb16_wrapper00_imx_address <= (others => 'Z');
        imx27_wb16_wrapper00_imx_data  <= (others => 'Z');
    -- read the RX counter value
        imx_read(RX_ID1_REG or SJA1000_ID,value,
        rstgen_syscon00_ext_clk,imx27_wb16_wrapper00_imx_cs_n,
        imx27_wb16_wrapper00_imx_oe_n, imx27_wb16_wrapper00_imx_eb0_n,
        imx27_wb16_wrapper00_imx_address(11 downto 0),imx27_wb16_wrapper00_imx_data,
        CLOCK_CYCLES);

        wait for HALF_PERIODE*10;

        -- write the RX counter value
        imx_write(RX_ID2_REG or SJA1000_ID,x"00AA",
        rstgen_syscon00_ext_clk,imx27_wb16_wrapper00_imx_cs_n,
        imx27_wb16_wrapper00_imx_oe_n, imx27_wb16_wrapper00_imx_eb0_n,
        imx27_wb16_wrapper00_imx_address(11 downto 0),imx27_wb16_wrapper00_imx_data,
        CLOCK_CYCLES);

     -- read the RX counter value
        imx_read(RX_ID1_REG or SJA1000_ID,value,
        rstgen_syscon00_ext_clk,imx27_wb16_wrapper00_imx_cs_n,
        imx27_wb16_wrapper00_imx_oe_n, imx27_wb16_wrapper00_imx_eb0_n,
        imx27_wb16_wrapper00_imx_address(11 downto 0),imx27_wb16_wrapper00_imx_data,
        CLOCK_CYCLES);

        wait for HALF_PERIODE*10;

    wait for HALF_PERIODE*10;
    assert false report "End of test" severity error;
    end process stimulis;

    simu_sja : process
    begin
        sja100000_sja_ad <= ( others => 'Z');
        wait until falling_edge(sja100000_sja_rd);
        wait for 50 ns;
        sja100000_sja_ad <= "01010111";
        wait until rising_edge(sja100000_sja_rd);
        wait for 30 ns;
    end process simu_sja;

    clockp : process
    begin
        rstgen_syscon00_ext_clk <= '1';
        wait for HALF_PERIODE;
        rstgen_syscon00_ext_clk <= '0';
        wait for HALF_PERIODE;
    end process clockp;

end architecture RTL;
