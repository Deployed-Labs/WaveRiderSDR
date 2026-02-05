"""
SDR Transmitter implementation for WaveRiderSDR.

Provides functionality for transmitting radio signals with regulatory compliance.
"""

import numpy as np
from typing import Optional
import logging
import warnings

from .config import SDRConfig


logger = logging.getLogger(__name__)


class SDRTransmitter:
    """
    Software Defined Radio Transmitter.
    
    Handles transmitting radio signals with safety checks and regulatory compliance.
    
    WARNING: Transmitting radio signals requires proper licensing and authorization
    in most jurisdictions. Users are responsible for compliance with all applicable
    regulations including FCC (USA), ETSI (Europe), and local telecommunications laws.
    """
    
    def __init__(self, config: Optional[SDRConfig] = None):
        """
        Initialize the SDR transmitter.
        
        Args:
            config: SDR configuration object
        """
        self.config = config or SDRConfig()
        self.is_transmitting = False
        self._device = None
        
        # Safety checks
        if not self.config.tx_enabled:
            warnings.warn(
                "Transmitter initialized but TX is disabled in config. "
                "Set tx_enabled=True to enable transmission.",
                UserWarning
            )
        
        logger.info(f"SDR Transmitter initialized with config: {self.config}")
        logger.warning(
            "REGULATORY WARNING: Ensure you have proper authorization to transmit "
            "on your chosen frequencies. Unauthorized transmission may be illegal."
        )
    
    def open(self) -> bool:
        """
        Open the SDR device for transmitting.
        
        Returns:
            True if device opened successfully
        """
        if not self.config.tx_enabled:
            logger.error("Cannot open transmitter: TX is disabled in config")
            return False
        
        # Validate configuration
        errors = self.config.validate()
        if errors:
            logger.error(f"Configuration validation failed: {errors}")
            return False
        
        try:
            # In a real implementation, this would open the actual SDR hardware
            logger.info(f"Opening SDR device for TX: {self.config.device_id}")
            logger.info(f"Setting center frequency: {self.config.center_frequency/1e6:.2f} MHz")
            logger.info(f"Setting sample rate: {self.config.sample_rate/1e6:.2f} MHz")
            logger.info(f"Setting TX gain: {self.config.tx_gain} dB")
            logger.info(f"Max TX power: {self.config.max_tx_power} W")
            
            # Verify frequency is allowed
            if not self.config.is_frequency_allowed_for_tx(self.config.center_frequency):
                logger.error(
                    f"Frequency {self.config.center_frequency/1e6:.2f} MHz is not in "
                    f"allowed TX bands: {self.config.allowed_tx_bands}"
                )
                return False
            
            self._device = "simulated_tx_device"
            logger.info("Transmitter opened successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to open transmitter: {e}")
            return False
    
    def close(self):
        """Close the SDR device and stop any transmission."""
        if self.is_transmitting:
            self.stop_transmitting()
        
        if self._device:
            logger.info("Closing SDR transmitter")
            self._device = None
    
    def set_frequency(self, frequency: float) -> bool:
        """
        Set the center frequency for transmitting.
        
        Args:
            frequency: Center frequency in Hz
            
        Returns:
            True if frequency is allowed and set successfully
        """
        if not self.config.is_frequency_allowed_for_tx(frequency):
            logger.error(
                f"Cannot set TX frequency to {frequency/1e6:.2f} MHz: "
                f"not in allowed bands"
            )
            return False
        
        self.config.center_frequency = frequency
        logger.info(f"TX frequency set to: {frequency/1e6:.2f} MHz")
        return True
    
    def set_gain(self, gain: float):
        """
        Set the transmitter gain.
        
        Args:
            gain: Gain in dB (0-100)
        """
        if gain < 0 or gain > 100:
            logger.warning(f"TX gain {gain} dB out of range, clamping to [0, 100]")
            gain = max(0, min(100, gain))
        
        self.config.tx_gain = gain
        logger.info(f"TX gain set to: {gain} dB")
    
    def set_sample_rate(self, rate: float):
        """
        Set the sample rate.
        
        Args:
            rate: Sample rate in Hz
        """
        self.config.sample_rate = rate
        logger.info(f"TX sample rate set to: {rate/1e6:.2f} MHz")
    
    def transmit_samples(self, samples: np.ndarray) -> bool:
        """
        Transmit IQ samples.
        
        Args:
            samples: Complex numpy array of IQ samples to transmit
            
        Returns:
            True if transmission successful
        """
        if not self._device:
            raise RuntimeError("Device not opened. Call open() first.")
        
        if not self.config.tx_enabled:
            logger.error("Cannot transmit: TX is disabled")
            return False
        
        # Safety check: verify samples are within reasonable power limits
        power = np.mean(np.abs(samples) ** 2)
        if power > 1.0:
            logger.warning(f"Sample power {power:.2f} exceeds 1.0, normalizing")
            samples = samples / np.sqrt(power)
        
        # In a real implementation, this would transmit to actual hardware
        logger.info(f"Transmitting {len(samples)} samples")
        logger.debug(f"Sample power: {power:.4f}")
        
        return True
    
    def start_transmitting(self):
        """Start continuous transmission mode."""
        if not self._device:
            raise RuntimeError("Device not opened. Call open() first.")
        
        if not self.config.tx_enabled:
            raise RuntimeError("Cannot start transmitting: TX is disabled")
        
        self.is_transmitting = True
        logger.info("Started continuous transmission")
        logger.warning("Transmitting - ensure compliance with regulations!")
    
    def stop_transmitting(self):
        """Stop continuous transmission mode."""
        self.is_transmitting = False
        logger.info("Stopped transmission")
    
    def generate_tone(self, frequency_offset: float, duration: float) -> np.ndarray:
        """
        Generate a tone signal for transmission.
        
        Args:
            frequency_offset: Frequency offset from center in Hz
            duration: Duration in seconds
            
        Returns:
            Complex numpy array of IQ samples
        """
        num_samples = int(duration * self.config.sample_rate)
        t = np.arange(num_samples) / self.config.sample_rate
        
        # Generate complex exponential (tone)
        samples = np.exp(2j * np.pi * frequency_offset * t)
        
        # Scale samples to appropriate power level
        # For IQ samples, power is mean(|samples|^2). A unit-power complex exponential has power=1
        # Scale to 50% of max power for safety margin
        target_amplitude = np.sqrt(0.5 * self.config.max_tx_power)
        samples = samples * target_amplitude
        
        logger.info(
            f"Generated tone: {frequency_offset/1e3:.2f} kHz offset, "
            f"{duration} seconds, {num_samples} samples"
        )
        
        return samples
    
    def get_allowed_frequencies(self) -> list:
        """
        Get list of allowed transmission frequency bands.
        
        Returns:
            List of tuples (start_freq, end_freq) in Hz
        """
        return self.config.allowed_tx_bands
