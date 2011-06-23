--
-- Copyright (c) ARMadeus Project 2011
--
-- GPIO Component
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
-- File          : pod_gpio.vhd
-- Created on    : 20/05/2011
-- Author        : Kevin JOLY joly.kevin25@gmail.com
--
--*********************************************************************
library IEEE;
use IEEE.STD_LOGIC_1164.all;
use ieee.numeric_std.all;

entity pod_gpio is
    generic (
                id : natural := 1;
                wb_size : natural := 16
            );
    port (
            -- Syscon signals
            gls_reset           : in std_logic;
            gls_clk             : in std_logic;
            -- Wishbone signals
            wbs_add             : in std_logic_vector (2 downto 0);
            wbs_writedata       : in std_logic_vector( wb_size-1 downto 0);
            wbs_readdata        : out std_logic_vector( wb_size-1 downto 0);
            wbs_strobe          : in std_logic;
            wbs_cycle           : in std_logic;
            wbs_write           : in std_logic;
            wbs_ack             : out std_logic;
            --interrupts
            interrupt           : out std_logic;
            --pod_gpio input/output
            gpio: inout std_logic_vector( 15 downto 0)
         );
end entity pod_gpio;

architecture pod_gpio_arch of pod_gpio is
    --State signal
    type state_type is (init, read, write);
    signal state_wb : state_type := init;
    signal GPIO_CONFIG : std_logic_vector( 15 downto 0) := (others => '1');
    signal GPIO_VALUE : std_logic_vector( 15 downto 0);
    signal gpio_old_value : std_logic_vector( 15 downto 0);
    signal GPIO_ENABLE_INTERRUPT : std_logic_vector( 15 downto 0);
    signal GPIO_INTERRUPT_STATUS : std_logic_vector( 15 downto 0);
    signal gpio_new_active_interrupt : std_logic_vector( 15 downto 0);
    signal GPIO_ACK_INTERRUPT : std_logic_vector( 15 downto 0);
    signal GPIO_INTERRUPT_EDGE_TYPE : std_logic_vector( 15 downto 0);
begin

    wishbone : process(gls_clk,gls_reset)
    begin
        if(gls_reset = '1') then
            state_wb <= init;
            GPIO_CONFIG <= (others => '1');
            GPIO_VALUE <= (others => '0');
            GPIO_ENABLE_INTERRUPT <= (others => '0');
            GPIO_INTERRUPT_EDGE_TYPE <= (others => '0');
            GPIO_ACK_INTERRUPT <= (others => '0');
        elsif(rising_edge(gls_clk)) then
            case state_wb is
                when init =>
                    GPIO_ACK_INTERRUPT <= (others => '0');
                    if((wbs_strobe and wbs_write) = '1') then
                        state_wb <= write;
                    elsif( wbs_strobe = '1' and wbs_write = '0') then
                        state_wb <= read;
                    end if;
                when write =>
                    if (wbs_strobe = '0') then
                        state_wb <= init;
                    else
                        case wbs_add is
                            when "001" =>
                                GPIO_CONFIG <= wbs_writedata;
                            when "010" =>
                                GPIO_VALUE <= wbs_writedata;
                            when "011" =>
                                GPIO_ENABLE_INTERRUPT <= wbs_writedata;
                            when "100" =>
                                GPIO_ACK_INTERRUPT <= wbs_writedata;
                            when "101" =>
                                GPIO_INTERRUPT_EDGE_TYPE <= wbs_writedata;
                            when others =>
                        end case;
                    end if;
                when read =>
                    if (wbs_strobe = '0') then
                        state_wb <= init;
                    end if;
            end case;
        end if;
    end process;

    irq_monitoring : process(gls_clk,gls_reset)
    begin
        if(gls_reset = '1') then
            GPIO_INTERRUPT_STATUS <= (others => '0');
            interrupt <= '0';
            gpio_old_value <= (others => '0');
        elsif(rising_edge(gls_clk)) then
            gpio_old_value <= gpio;
            if (not (GPIO_INTERRUPT_STATUS = gpio_new_active_interrupt)) then
                GPIO_INTERRUPT_STATUS <= gpio_new_active_interrupt;
                if (GPIO_ACK_INTERRUPT = x"0000") then
                    interrupt <= '1';
                end if;
            else
                interrupt <= '0';
            end if;
        end if;
    end process irq_monitoring;

    -- gpio write
    gpio_output : for i in 0 to 15 generate
        gpio(i) <= GPIO_VALUE(i) when GPIO_CONFIG(i) = '0' else 'Z';
    end generate;

    wbs_readdata( wb_size-1 downto 0) <=    std_logic_vector(to_unsigned(id, wb_size))  when wbs_add = "000" else
                                            GPIO_CONFIG                                 when wbs_add = "001" else
                                            gpio                                        when wbs_add = "010" else
                                            GPIO_ENABLE_INTERRUPT                       when wbs_add = "011" else
                                            GPIO_INTERRUPT_STATUS                       when wbs_add = "100" else
                                            GPIO_INTERRUPT_EDGE_TYPE                    when wbs_add = "101" else
                                            (others => '0');

    gpio_new_active_interrupt <= (((GPIO_INTERRUPT_STATUS AND not GPIO_ACK_INTERRUPT) OR ((gpio XOR gpio_old_value) and not (gpio XOR GPIO_INTERRUPT_EDGE_TYPE))) AND GPIO_ENABLE_INTERRUPT);

end architecture pod_gpio_arch;


