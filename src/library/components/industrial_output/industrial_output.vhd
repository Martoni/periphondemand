--
-- Copyright (c) ARMadeus Project 2009
--
-- Wishbone component that drive sn74hc594 8 bits shift register
--
-- This program is free software; you can redistribute it and/or modify
-- it under the terms of the GNU Lesser General Public License as published by
-- the Free Software Foundation; either version 2, or (at your option)
-- any later version.
--
-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU Lesser General Public License for more details.
--
-- You should have received a copy of the GNU Lesser General Public License
-- along with this program; if not, write to the Free Software
-- Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
--*********************************************************************
--
-- File          : industrial_output.vhd
-- Created on    : 08/06/2009
-- Author        : Fabien Marteau <fabien.marteau@armadeus.com>
-- 
--*********************************************************************

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.numeric_std.all;

---------------------------------------------------------------------------
Entity industrial_output is 
---------------------------------------------------------------------------
generic(
    id       : natural := 1;    -- identification register value
    wb_size  : natural := 16;   -- Data port size for wishbone
    serial_speed : natural := 1000; -- serial speed in kHz
    clk_freq : natural := 133000 -- fpga clock speed in kHz
);
port 
(
    -- Syscon signals
    reset    : in std_logic ; -- reset
    clk      : in std_logic ; -- general clock
    -- Wishbone signals
    wbs_add       : in std_logic ;
    wbs_writedata : in std_logic_vector( wb_size-1 downto 0);
    wbs_readdata  : out std_logic_vector( wb_size-1 downto 0);
    wbs_strobe    : in std_logic ;
    wbs_cycle      : in std_logic ;
    wbs_write     : in std_logic ;
    wbs_ack       : out std_logic;
    -- sn74hc594 signals
    reset_n       : out std_logic;
    rclk          : out std_logic;
    srclk         : out std_logic;
    ser           : out std_logic;
    qh            : in std_logic 
);
end entity;

---------------------------------------------------------------------------
Architecture industrial_output_1 of industrial_output is
---------------------------------------------------------------------------

    -- usefull constant
    constant ZERO : std_logic_vector(15 downto 0) := x"0000";

    -- state machine
    type state_type is (out_void, out_init, out_write_value, out_write_pulse, out_out);
    signal state_reg : state_type;
    signal next_state: state_type;

    -- registers addresses
    constant CTRL_DATA : std_logic := '0';
    constant ID_ADDR   : std_logic := '1';

    -- registers
    signal data     : std_logic_vector(7 downto 0);

    signal data_reg : std_logic_vector(7 downto 0);
    signal ser_reg : std_logic ;
    signal spi_count_reg: natural range 0 to 10;


    signal data_next    : std_logic_vector(7 downto 0);
    signal ser_next: std_logic ;

    -- spi clock
    signal spi_clk : std_logic ;
    signal spi_clk_rise : std_logic ;
    signal spi_clk_fall : std_logic ;

    -- state machine signals 
    signal data_wrote : std_logic ;

    --   
    signal read_ack : std_logic ;
    signal write_ack : std_logic ;
    signal enable_spi_clk : std_logic ;

begin

    wbs_ack <= write_ack or read_ack;

    -- read process
    read_p : process (clk, reset)
    begin
        if reset = '1' then
            wbs_readdata <= ( others => '0');
        elsif rising_edge(clk) then
            if (wbs_strobe and (not wbs_write) and wbs_cycle) = '1' then
                read_ack <= '1';
                case wbs_add is
                    when CTRL_DATA => 
                        wbs_readdata <= ZERO(15 downto 8)&data;
                    when ID_ADDR   =>
                        wbs_readdata <= std_logic_vector(to_unsigned(id,wb_size)); 
                    when others => 
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
        variable wrote_v  : std_logic;
    begin
        if reset = '1' then
            data <= (others => '0');
            wrote_v := '0';
            write_ack <= '0';
        elsif rising_edge(clk) then
            write_ack <= '0';
            data_wrote <= '0';
            if (wbs_strobe and wbs_write and wbs_cycle) = '1' then
                write_ack <= '1';
                data <= wbs_writedata(7 downto 0);
                wrote_v := '1';
            elsif wrote_v = '1' then
                data_wrote <= '1';
                wrote_v := '0';
            end if;
        end if;
    end process write_p;

    -- clock generator
    clock_divider : process (clk, reset)
        variable count : natural range 0 to (2**wb_size)-1;
    begin
        if reset = '1' then
            count := 0;
            spi_clk <= '0';
            spi_clk_rise <= '0';
            spi_clk_fall <= '0';
            spi_count_reg <= 0;
        elsif rising_edge(clk) then
            if enable_spi_clk = '1' then
                if (count <= (clk_freq / (2*serial_speed))) then
                    count := count + 1;
                    spi_clk <= spi_clk;
                    spi_clk_rise <= '0';
                    spi_clk_fall <= '0';
                else
                    count := 0;
                    spi_clk <= not spi_clk;
                    if spi_clk = '0' then
                        spi_count_reg <= spi_count_reg + 1;
                        spi_clk_rise <= '1';
                        spi_clk_fall <= '0';
                    else
                        spi_clk_rise <= '0';
                        spi_clk_fall <= '1';
                    end if;
                end if;
            else
                spi_count_reg <= 0;
                spi_clk <= '0';
                spi_clk_fall <= '0';
                spi_clk_rise <= '0';
            end if;
        end if;
    end process clock_divider;

    --state register
    spi_state_register_p : process (clk, reset)
    begin
        if reset = '1' then
            state_reg <= out_void;
            data_reg  <= (others => '0'); 
            ser_reg   <= '0';
        elsif rising_edge(clk) then
            state_reg <= next_state;
            ser_reg   <= ser_next;
            data_reg  <= data_next;
        end if;
    end process spi_state_register_p;

    -- next-state logic
    nstate_p : process( state_reg, spi_clk_fall, spi_clk_rise, 
                        data_wrote,spi_count_reg )
    begin
        next_state <= state_reg;
        case state_reg is
            when out_void =>
                    if data_wrote = '1' then
                        next_state <= out_init;
                    end if;
            when out_init =>
                    if spi_clk_fall = '1' then
                        next_state <= out_write_value;
                    end if;
            when out_write_value =>
                    if spi_clk_rise = '1' then
                        next_state <= out_write_pulse;
                    end if;
            when out_write_pulse =>
                    if (spi_count_reg < 9) and spi_clk_fall = '1' then 
                        next_state <= out_write_value;
                    elsif (spi_count_reg >= 9) then
                        next_state <= out_out;
                    end if;
            when out_out =>
                    if spi_count_reg < 10 then
                        next_state <= out_out;
                    else
                        next_state <= out_void;
                    end if;
            when others => 
                    next_state <= out_void;
        end case;
    end process nstate_p;

    -- output logic
    output_p : process (state_reg, spi_clk, data_reg, ser_reg, spi_count_reg,data)
    begin
        ser_next <= ser_reg;
        data_next <= data_reg;
        case state_reg is
            when out_void => 
                rclk   <= '0';
                srclk  <= '1';
                ser_next    <= '0';
                enable_spi_clk <= '0';
                data_next <= data;
            when out_init => 
                rclk   <= '0';
                srclk  <= '1';
                ser_next    <= '0';
                enable_spi_clk <= '1';
            when out_write_value =>
                rclk   <= '0';
                srclk  <= spi_clk;
                ser_next  <= data_reg(7);
                if spi_clk_rise = '1' then
                    data_next <= data_reg(6 downto 0)&'0';
                end if; 
                enable_spi_clk <= '1';
            when out_write_pulse =>
                rclk   <= '0';
                srclk  <= spi_clk;
                ser_next <= ser_reg;
                data_next <= data_reg;
                enable_spi_clk <= '1';
            when out_out => 
                rclk   <= '1'; -- refresh output
                srclk  <= '1';
                ser_next <= ser_reg;
                data_next <= data_reg;
                enable_spi_clk <= '1';
            when others => 
                rclk   <= '0';
                srclk  <= '1';
                ser_next    <= '0';
                enable_spi_clk <= '0';
        end case;
    end process output_p;

    ser    <= ser_reg;
    reset_n <= '1';

end architecture industrial_output_1;

