---------------------------------------------------------------------------
-- Company     : ARMadeus Systems
-- Author(s)   : Fabien Marteau <fabien.marteau@armadeus.com>
--
-- Creation Date : 30/04/2009
-- File          : sp_vision_configure.vhd
--
-- Abstract : This IP manage input serialized by the
-- industrial 8-digital-input serializer : SN65HVS882
--
---------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.numeric_std.all;

---------------------------------------------------------------------------
Entity sp_vision_configure is
---------------------------------------------------------------------------
    generic(
        id       : natural := 1;    -- identification register value
        wb_size  : natural := 16;   -- Data port size for wishbone
        clk_freq : natural := 100000 -- fpga clock speed
    );
    port
    (
        -- Syscon signals
        reset    : in std_logic ; -- reset
        clk      : in std_logic ; -- general clock
        -- Wishbone signals
        wbs_add       : in std_logic_vector( 1 downto 0) ; -- address bus
        wbs_writedata : in std_logic_vector( wb_size-1 downto 0);
        wbs_readdata  : out std_logic_vector( wb_size-1 downto 0);
        wbs_strobe    : in std_logic ;
        wbs_cycle     : in std_logic ;
        wbs_write     : in std_logic ;
        wbs_ack       : out std_logic;
        -- selectMap port
        selectmap_data      : inout std_logic_vector( wb_size-1 downto 0);
        selectmap_csi_n     : inout std_logic ;
        selectmap_rdwr_n    : inout std_logic ;
        selectmap_cclk      : inout std_logic ;
        selectmap_program_n : inout std_logic ;
        selectmap_init_n    : in std_logic ;
        selectmap_busy      : in std_logic ;
        selectmap_done      : in std_logic
    );
end entity;

---------------------------------------------------------------------------
Architecture sp_vision_configure_1 of sp_vision_configure is
---------------------------------------------------------------------------
    -- usefull constant
    constant ZERO : std_logic_vector(15 downto 0) := x"0000";
    constant CLK_PULSE_LENGHT : natural := 2; -- clk pulse lenght
    -- Registers addresses
    constant ID_REG_ADDR     : std_logic_vector( 1 downto 0) := "00";
    constant CONFIG_REG_ADDR : std_logic_vector( 1 downto 0) := "01";
    constant STATUS_REG_ADDR : std_logic_vector( 1 downto 0) := "10";
    constant DATA_REG_ADDR   : std_logic_vector( 1 downto 0) := "11";
    -- Registers
    signal config_reg   : std_logic_vector( wb_size-1 downto 0);
    signal status_reg   : std_logic_vector( wb_size-1 downto 0);
    signal data_reg     : std_logic_vector( wb_size-1 downto 0);

    -- internal ctrl signals
    signal read_ack : std_logic ;
    signal write_ack: std_logic ;

    signal cclk_sig : std_logic ;
    signal cclk_trig : std_logic ;

    signal data_inverter : std_logic_vector( wb_size-1 downto 0);

begin

    -- config_reg :
    -- |15|14|13|12|11|10|9|8|7|6|5| 4 |3 |  2  |    1    |  0   |
    -- |X |X |X |X |X |X |X|X|X|X|X|CLK|X|CSI_n|PROGRAM_n|RDWR_n|
    -- If CLK=1, system clock is routed on CCLK and all configuration output
    -- are high Z

    selectmap_rdwr_n    <= config_reg(0) when config_reg(4) = '0' else 'Z';
    selectmap_program_n <= config_reg(1) when config_reg(4) = '0' else 'Z';
    selectmap_csi_n     <= config_reg(2) when config_reg(4) = '0' else 'Z';
    selectmap_cclk      <= cclk_sig when config_reg(4) = '0' else clk;
    data_inverter      <= data_reg when config_reg(4) = '0' else (others => 'Z');

    selectmap_data(0)  <= data_inverter(7);
    selectmap_data(1)  <= data_inverter(6);
    selectmap_data(2)  <= data_inverter(5);
    selectmap_data(3)  <= data_inverter(4);
    selectmap_data(4)  <= data_inverter(3);
    selectmap_data(5)  <= data_inverter(2);
    selectmap_data(6)  <= data_inverter(1);
    selectmap_data(7)  <= data_inverter(0);

    selectmap_data(8)  <= data_inverter(15);
    selectmap_data(9)  <= data_inverter(14);
    selectmap_data(10) <= data_inverter(13);
    selectmap_data(11) <= data_inverter(12);
    selectmap_data(12) <= data_inverter(11);
    selectmap_data(13) <= data_inverter(10);
    selectmap_data(14) <= data_inverter(9);
    selectmap_data(15) <= data_inverter(8);

    -- Status register
    -- |15|14|13|12|11|10|9|8|7|6|5|4|3|   2  |  1 | 0  |
    -- |X |X |X |X |X |X |X|X|X|X|X|X|X|INIT_n|BUSY|DONE|
    status_reg <= ZERO(15 downto 3)&selectmap_init_n&selectmap_busy&selectmap_done;

    -- read process
    read_p : process (clk, reset)
    begin
        if reset = '1' then
            wbs_readdata <= (others => '0');
        elsif rising_edge(clk) then
            if ( wbs_strobe and (not wbs_write) and wbs_cycle) = '1' then
                read_ack <= '1';
                case wbs_add is
                    when ID_REG_ADDR =>
                        wbs_readdata <= std_logic_vector(to_unsigned(id,wb_size));
                    when CONFIG_REG_ADDR =>
                        wbs_readdata <= config_reg;
                    when STATUS_REG_ADDR =>
                        wbs_readdata <= status_reg;
                    when DATA_REG_ADDR =>
                        wbs_readdata <= data_reg;
                    when others =>
                        wbs_readdata <= ZERO;
                end case;
            else
                read_ack <= '0';
                wbs_readdata <= (others => '0');
            end if;
        end if;
    end process read_p;

    -- write process
    write_p : process (clk, reset)
    begin
        if reset = '1' then
            config_reg <= x"0007";
            data_reg   <= (others => '0');
        elsif rising_edge(clk) then
            write_ack <= '0';
            if (wbs_strobe and wbs_write and wbs_cycle) = '1' then
                write_ack <= '1';
                case wbs_add is
                    when CONFIG_REG_ADDR =>
                        config_reg <= wbs_writedata;
                        data_reg <= data_reg;
                    when DATA_REG_ADDR =>
                        config_reg <= config_reg;
                        data_reg <= wbs_writedata;
                    when others =>
                        config_reg <= config_reg;
                        data_reg <= data_reg;
                end case;
            end if;
        end if;
    end process write_p;

    -- CCLK trigger generator
    cclk_p : process (clk, reset)
    begin
        if reset = '1' then
            cclk_trig <= '0';
        elsif rising_edge(clk) then
                if (wbs_add = DATA_REG_ADDR) and
                   (wbs_strobe = '1') and (wbs_write = '1') then
                    cclk_trig <= '1';
                else
                    cclk_trig <= '0';
                end if;
        end if;
    end process cclk_p;

    cclk_gen : process (clk, reset)
        variable counter : natural range 0 to (CLK_PULSE_LENGHT+1);
    begin
        if reset = '1' then
            cclk_sig <= '0';
            counter := 0;
        elsif rising_edge(clk) then
            if cclk_trig = '1' then
                counter := 0;
                cclk_sig <= '0';
            elsif counter < (CLK_PULSE_LENGHT/2) then
                counter := counter +1;
                cclk_sig <= '0';
            elsif counter < (CLK_PULSE_LENGHT) then
                counter := counter +1;
                cclk_sig <= '1';
            else
                cclk_sig <= '0';
            end if;
        end if;
    end process cclk_gen;

    wbs_ack <= read_ack or write_ack;

end architecture sp_vision_configure_1;

