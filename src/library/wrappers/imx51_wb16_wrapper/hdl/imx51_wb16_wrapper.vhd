-------------------------------------------------------------------------------
--
--  File          :  imx51_wb16_wrapper.vhd
--  Related files :  (none)
--
--  Author(s)     :  Fabien Marteau <fabien.marteau@armadeus.com>
--  Project       :  i.MX51 wrapper to Wishbone bus
--
--  Creation Date :  17/12/2010
--
--  Description   :  This is the top file of the IP
-------------------------------------------------------------------------------
--  Modifications :
--
-------------------------------------------------------------------------------

library IEEE;
  use IEEE.std_logic_1164.all;
  use IEEE.numeric_std.all;

---------------------------------------------------------------------------
Entity imx51_wb16_wrapper is
---------------------------------------------------------------------------
port
(
    -- i.MX Signals
    imx_da    : inout std_logic_vector(15 downto 0);
    imx_cs_n  : in std_logic;
    imx_rw    : in std_logic ;
    imx_adv   : in std_logic ;

    -- Global Signals
    gls_reset : in std_logic;
    gls_clk   : in std_logic;

    -- Wishbone interface signals
    wbm_address    : out std_logic_vector(15 downto 0);  -- Address bus
    wbm_readdata   :  in std_logic_vector(15 downto 0);  -- Data bus for read access
    wbm_writedata  : out std_logic_vector(15 downto 0);  -- Data bus for write access
    wbm_strobe     : out std_logic;                      -- Data Strobe
    wbm_write      : out std_logic;                      -- Write access
    wbm_ack        :  in std_logic;                      -- acknowledge
    wbm_cycle      : out std_logic                       -- bus cycle in progress
);
end entity;

---------------------------------------------------------------------------
Architecture RTL of imx51_wb16_wrapper is
---------------------------------------------------------------------------

    signal write      : std_logic;
    signal read       : std_logic;
    signal strobe     : std_logic;
    signal writedata  : std_logic_vector(15 downto 0);
    signal address    : std_logic_vector(15 downto 0);

begin

    -- ----------------------------------------------------------------------------
    --  External signals synchronization process
    -- ----------------------------------------------------------------------------
    process(gls_clk, gls_reset)
    begin
      if(gls_reset='1') then
        writedata <= (others => '0');
        address   <= (others => '0');
      elsif(rising_edge(gls_clk)) then
        if (imx_adv = '0') then
            address <= imx_da;
        else
            writedata <= imx_da;
        end if;
      end if;
    end process;
    strobe  <= not (imx_cs_n);
    write   <= (not (imx_cs_n)) and (not(imx_rw));
    read    <= (not (imx_cs_n)) and imx_rw;

    wbm_address    <= address;
    wbm_writedata  <= writedata when (write = '1') else (others => '0');
    wbm_strobe     <= strobe;
    wbm_write      <= write;
    wbm_cycle      <= strobe;

    imx_da <= wbm_readdata when ((read = '1') and (strobe = '1')) else (others => 'Z');

end architecture RTL;
