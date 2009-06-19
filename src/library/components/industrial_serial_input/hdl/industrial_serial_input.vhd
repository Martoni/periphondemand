---------------------------------------------------------------------------
-- Company     : ARMades Systems
-- Author(s)   : Fabien Marteau <fabien.marteau@armadeus.com>
-- 
-- Creation Date : 30/04/2009
-- File          : industrial_serial_input.vhd
--
-- Abstract : This IP manage input serialized by the 
-- industrial 8-digital-input serializer : SN65HVS882
--
---------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.numeric_std.all;

---------------------------------------------------------------------------
Entity industrial_serial_input is 
---------------------------------------------------------------------------
    generic(
        id       : natural := 1;    -- identification register value
        wb_size  : natural := 16;   -- Data port size for wishbone
        clk_freq : natural := 133000 -- fpga clock speed
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
        wbs_cycle      : in std_logic ;
        wbs_write     : in std_logic ;
        wbs_ack       : out std_logic;
        -- interrupt
        interrupt : out std_logic ; -- interrupt signal
        -- SN65HVS882 controls signals
        spi_sip  : out std_logic ;
        spi_ld_n : out std_logic ;
        spi_clk  : out std_logic ; -- SPI clock
        spi_sop  : in  std_logic 
    );
end entity;


---------------------------------------------------------------------------
Architecture industrial_serial_input_1 of industrial_serial_input is
---------------------------------------------------------------------------

    -- usefull constants
    constant ZERO : std_logic_vector( 31 downto 0) := (others => '0');

    -- states type
    type state is (spi_init_state,spi_read7_state,spi_read_state,spi_end_state);
    signal state_reg      : state;
    signal next_state_reg : state;

    -- registers addresses
    constant REG_DATA      : std_logic_vector( 1 downto 0) := "00"; -- |x[15:9]|int_en|data[7:0]
    constant REG_READ_PER  : std_logic_vector( 1 downto 0) := "01"; -- read period = reg x bus period
    constant REG_BUS_PER   : std_logic_vector( 1 downto 0) := "10"; -- bus period =  reg x clock period
    constant REG_ID        : std_logic_vector( 1 downto 0) := "11"; -- identification register 

    constant BUS_PER_DFLT : std_logic_vector(15 downto 0) := x"010A";
    constant READ_PER_DFLT: std_logic_vector(15 downto 0) := x"0000";  

    -- registers
    signal data_reg : std_logic_vector( 7 downto 0):= x"00";
    signal int_en : std_logic ;
    signal read_per : std_logic_vector( wb_size-1 downto 0);
    signal bus_per  : std_logic_vector( wb_size-1 downto 0);

    signal data   : std_logic_vector( 7 downto 0):= x"00";

    -- local clocks signals
    signal local_clk : std_logic ;
    signal clock_rise_pulse : std_logic ;
    signal clock_fall_pulse : std_logic ;

    -- spi signals
    signal spi_read_pulse : std_logic ;
    signal spi_read_count : natural range 0 to 8;

    -- wisbone acks
    signal read_ack : std_logic ;
    signal write_ack : std_logic ;

begin

    -- read process
    read_p : process (clk,reset)
    begin
        if reset = '1' then
            wbs_readdata <= (others => '0');
        elsif rising_edge(clk) then
            if (wbs_strobe and (not wbs_write) and wbs_cycle) = '1' then
                read_ack <= '1';
                case wbs_add is
                    when REG_DATA     => 
                        -- change data_reg bits order to match card route
                        wbs_readdata <=  
                            ZERO(6 downto 0)&int_en&
                            data_reg(5)&
                            data_reg(6)&
                            data_reg(7)&
                            data_reg(4 downto 0);
                    when REG_READ_PER => 
                        wbs_readdata <= read_per;
                    when REG_BUS_PER  => 
                        wbs_readdata <= bus_per; 
                    when REG_ID       => 
                        wbs_readdata <=  std_logic_vector(to_unsigned(id,wb_size));
                    when others       => 
                        wbs_readdata <= (others => '0');
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
            int_en <= '0';
            -- defaut values
            bus_per <= BUS_PER_DFLT; -- 266 x 3.759 = 1MHz
            read_per <= READ_PER_DFLT;
        elsif rising_edge(clk) then
            if (wbs_strobe and wbs_write and wbs_cycle) = '1' then
                case wbs_add is
                    when REG_DATA     => 
                        int_en <= wbs_writedata(8);
                        write_ack <= '1';
                    when REG_READ_PER =>
                        read_per  <= wbs_writedata;
                        write_ack <= '1';
                    when REG_BUS_PER  =>
                        if wbs_writedata = x"0000" then
                            bus_Per <= x"0001";
                        else
                            bus_per   <= wbs_writedata;
                        end if;
                        write_ack <= '1';
                    when others => 
                        write_ack <= '1';
                end case;
            else
                write_ack <= '0';
            end if;
             
        end if;
    end process write_p;

    wbs_ack <= read_ack or write_ack;

    -- SPI clock generator
    clock_divider : process (clk,reset)
        variable count : natural range 0 to (2**13)-1;
    begin
        if reset = '1' then
            count := 0;
            local_clk <= '0';
            clock_rise_pulse <= '0';
            clock_fall_pulse <= '0';
        elsif rising_edge(clk) then
            if (count < to_integer(unsigned(bus_per))) then
                count := count + 1;
                local_clk <= local_clk;
                clock_rise_pulse <= '0';
                clock_fall_pulse <= '0';
            else 
                clock_fall_pulse <= local_clk;
                clock_rise_pulse <= not local_clk;
                local_clk <= not local_clk;
                count := 0;
            end if;
        end if;
    end process clock_divider;

    -- read_pulse generator
    read_pulse_p : process (clk,reset)
        variable count : natural range 0 to (2**wb_size)-1;
    begin
        if reset = '1' then
            count := 0;
            spi_read_pulse <= '0';
        elsif rising_edge(clk) then
                if (count <= to_integer(unsigned(read_per))) then
                    if clock_rise_pulse = '1' then
                        count := count + 1;
                        spi_read_pulse <= spi_read_pulse;
                    elsif clock_fall_pulse = '1' then
                        spi_read_pulse <= '0';
                    end if;
                elsif clock_rise_pulse = '1' then
                    count := 0;
                    spi_read_pulse <= '1';
                end if;
        end if;
    end process read_pulse_p;

    -- interrupt management process
    interrupt_p : process (clk,reset)
    begin
        if reset = '1' then
            interrupt <= '0';
        elsif rising_edge(clk) then
            if data_reg /= data and (state_reg = spi_end_state) then
                interrupt <= int_en; -- rise interrupt if data reg is changed 
            elsif (read_ack = '1') and (wbs_add = REG_DATA) then
                interrupt <= '0'; -- reset interrupt when data register is read
            end if;
        end if;
    end process interrupt_p;

    ----------------------------
    -- spi read state machine --
    ----------------------------

    -- state register
    spi_state_register_p : process (clk,reset)
    begin
        if reset = '1' then
            state_reg <= spi_init_state; 
        elsif rising_edge(clk) then
            state_reg <= next_state_reg;
        end if;
    end process spi_state_register_p;

    -- next-state logic
    nstate_p : process (state_reg,spi_read_pulse,clock_rise_pulse,spi_read_count)
    begin
        case state_reg is
            when spi_init_state  => 
                if spi_read_pulse = '1' then
                    next_state_reg <= spi_read7_state;
                else
                    next_state_reg <= spi_init_state;
                end if;
            when spi_read7_state => 
                if spi_read_pulse = '0' and clock_rise_pulse = '1' then
                    next_state_reg <= spi_read_state;
                else
                    next_state_reg <= spi_read7_state;
                end if;
            when spi_read_state  =>
                if spi_read_count > 7  then
                    next_state_reg <= spi_end_state;
                else
                    next_state_reg <= spi_read_state;
                end if;
            when spi_end_state   =>
                    next_state_reg <= spi_init_state;
            when others => 
                next_state_reg <= spi_init_state;
        end case;
    end process nstate_p;

    -- output logic
    --output_p : process (state_reg,spi_sop,data,local_clk)
    output_p : process (clk,reset)
    begin
        if reset = '1' then 
            data <= (others => '0');
            spi_clk <= '0';
        elsif rising_edge(clk) then
            case state_reg is
                when spi_init_state  => 
                    data <= (others => '0');
                    spi_clk <= '0';
                when spi_read7_state =>
                    spi_clk <= local_clk; 
                    data(0) <= spi_sop;
                when spi_read_state  =>
                    spi_clk <= local_clk;
                    if clock_fall_pulse = '1' then
                        data <= data(6 downto 0)&spi_sop;
                    end if;
                when spi_end_state => 
                        data_reg <= data;
                when others => 
                    spi_clk <= local_clk;
            end case;
        end if;
    end process output_p;

    spi_ld_n <= '0' when state_reg = spi_read7_state else '1' ;
    spi_sip  <= '1';

    -- read count
    read_count_p : process (clk, reset)
    begin
        if reset = '1' then
            spi_read_count <= 0;
        elsif rising_edge(clk) then
            if state_reg = spi_read_state then
                if clock_rise_pulse = '1' then
                    spi_read_count <= spi_read_count + 1;
                else 
                    spi_read_count <= spi_read_count;
                end if;
            else
                spi_read_count <= 0;
            end if;
        end if;
    end process read_count_p;

end architecture industrial_serial_input_1;

