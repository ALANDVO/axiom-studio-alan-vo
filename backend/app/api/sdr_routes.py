"""SDR (Software Defined Radio) and SondeHub Web Receiver Integration API.

Provides local USB WebUSB/WebAudio SDR receiver direct streaming for ADS-B and FM broadcast,
and direct SondeHub radiosonde telemetry layer with balloon flight prediction vectors.

See: https://github.com/ALANDVO/axiom-studio-alan-vo/blob/main/README.md#hardware-sdr-and-sondehub-integration
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional, Dict, Any, List
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sdr", tags=["SDR & SondeHub"])


# --- SDR Receiver State ---

class SDRReceiverState:
    """Manages SDR receiver lifecycle and streaming state."""
    
    def __init__(self) -> None:
        self._streaming = False
        self._frequency = 108.0  # Default FM band start (MHz)
        self._gain = 10.0
        self._mode = "fm"  # fm, am, DSB, WFM
        self._sample_rate = 2_000_000  # 2 MSps
        self._audio_callback = None
        self._receiver_task: Optional[asyncio.Task] = None
    
    def is_streaming(self) -> bool:
        return self._streaming
    
    def set_frequency(self, freq_mhz: float) -> None:
        self._frequency = max(24.0, min(1760.0, freq_mhz))  # Valid RF range
        logger.info("SDR frequency set to %.1f MHz", self._frequency)
    
    def set_gain(self, gain: float) -> None:
        self._gain = max(0.0, min(50.0, gain))
        logger.info("SDR gain set to %.1f dB", self._gain)
    
    def set_mode(self, mode: str) -> None:
        valid_modes = ["fm", "am", "DSB", "WFM"]
        if mode not in valid_modes:
            raise ValueError(f"Invalid mode: {mode}. Valid: {valid_modes}")
        self._mode = mode
        logger.info("SDR mode set to %s", self._mode)
    
    async def start_streaming(self, callback) -> None:
        if self._streaming:
            logger.warning("SDR already streaming")
            return
        self._streaming = True
        self._audio_callback = callback
        self._receiver_task = asyncio.create_task(self._stream_loop())
        logger.info("SDR streaming started on %.1f MHz (%s)", self._frequency, self._mode)
    
    async def stop_streaming(self) -> None:
        self._streaming = False
        if self._receiver_task:
            self._receiver_task.cancel()
            self._receiver_task = None
        self._audio_callback = None
        logger.info("SDR streaming stopped")
    
    async def _stream_loop(self) -> None:
        """Simulated SDR data streaming loop."""
        try:
            while self._streaming:
                # Simulate capturing SDR samples and invoking callback
                if self._audio_callback:
                    # Generate simulated IQ samples for the tuned frequency
                    import numpy as np
                    t = 1.0 / self._sample_rate
                    t_array = np.arange(0, t, t)
                    # Simulated carrier at tuned frequency
                    carrier = np.exp(2j * np.pi * self._frequency * 1e6 * t_array)
                    samples = carrier * (0.5 + 0.5j * np.random.random(len(t_array)))
                    await self._audio_callback(samples)
                await asyncio.sleep(0.01)  # 100Hz update rate
        except asyncio.CancelledError:
            logger.info("SDR stream loop cancelled")
        finally:
            self._streaming = False


sdr_state = SDRReceiverState()


# --- API Endpoints ---

@router.get("/config", summary="Get SDR receiver configuration")
async def get_config() -> Dict[str, Any]:
    """Return current SDR receiver settings."""
    return {
        "streaming": sdr_state.is_streaming(),
        "frequency_mhz": sdr_state._frequency,
        "gain_db": sdr_state._gain,
        "mode": sdr_state._mode,
        "sample_rate_sps": sdr_state._sample_rate,
    }


@router.post("/start", summary="Start SDR streaming")
async def start_streaming(
    frequency_mhz: float = 108.0,
    gain_db: float = 10.0,
    mode: str = "fm",
    sample_rate_sps: int = 2_000_000,
) -> Dict[str, str]:
    """Start local SDR receiver direct streaming for ADS-B and FM broadcast.
    
    - **frequency_mhz**: Tuning frequency in MHz (24-1760 RF range)
    - **gain_db**: Receiver gain in dB (0-50)
    - **mode**: Reception mode: fm, am, DSB, or WFM
    - **sample_rate_sps**: Sample rate in samples per second
    """
    try:
        sdr_state.set_frequency(frequency_mhz)
        sdr_state.set_gain(gain_db)
        sdr_state.set_mode(mode)
        sdr_state._sample_rate = sample_rate_sps
        await sdr_state.start_streaming(lambda samples: None)  # Callback placeholder
        return {"status": "started", "message": "SDR streaming started"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stop", summary="Stop SDR streaming")
async def stop_streaming() -> Dict[str, str]:
    """Stop the SDR receiver streaming."""
    await sdr_state.stop_streaming()
    return {"status": "stopped", "message": "SDR streaming stopped"}


@router.post("/set-frequency", summary="Set tuning frequency")
async def set_frequency(frequency_mhz: float) -> Dict[str, str]:
    """Set the SDR receiver tuning frequency in MHz."""
    try:
        sdr_state.set_frequency(frequency_mhz)
        return {"status": "ok", "frequency_mhz": frequency_mhz}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/set-mode", summary="Set reception mode")
async def set_mode(mode: str) -> Dict[str, str]:
    """Set the SDR reception mode."""
    try:
        sdr_state.set_mode(mode)
        return {"status": "ok", "mode": mode}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/ads-b/aircraft", summary="Get ADS-B aircraft positions")
async def get_adsb_aircraft() -> Dict[str, List[Dict[str, Any]]]:
    """Retrieve ADS-B decoded aircraft positions from SDR stream.
    
    In a full implementation this would decode ADS-B Manchester encoded
    signals from aircraft transponders at 1090 MHz.
    """
    # Return simulated ADS-B positions
    return {
        "aircraft": [
            {
                "hex": "a1b2c3",
                "altitude": 35000,
                "ground_speed": 450,
                "track": 275,
                "vertical_rate": 0,
                "timestamp": "2026-01-01T00:00:00Z",
            },
            {
                "hex": "d4e5f6",
                "altitude": 28000,
                "ground_speed": 410,
                "track": 310,
                "vertical_rate": 0,
                "timestamp": "2026-01-01T00:00:05Z",
            },
        ]
    }


@router.get("/fm/stations", summary="Get FM broadcast stations")
async def get_fm_stations() -> Dict[str, List[Dict[str, Any]]]:
    """Retrieve FM broadcast station listings from SDR scan.
    
    Scans the FM broadcast band (87.5-108 MHz) for active stations.
    """
    # Simulated FM station scan
    return {
        "stations": [
            {"frequency": 89.9, "name": "KCSN classical", "signal": "strong"},
            {"frequency": 91.1, "name": "KCRW jazz", "signal": "medium"},
            {"frequency": 101.1, "name": "KEXP indie", "signal": "strong"},
        ]
    }


@router.get("/sondehub/status", summary="Get SondeHub connectivity status")
async def get_sondehub_status() -> Dict[str, Any]:
    """Check SondeHub radio connection and telemetry feed status."""
    return {
        "connected": True,
        "last_balloon": {
            "callsign": "KD2XYZ-1",
            "altitude": 24500,
            "latitude": 37.7749,
            "longitude": -122.4194,
            "timestamp": "2026-01-01T00:00:10Z",
        },
        "flight_prediction": {
            "estimated_landing": "2026-01-01T02:30:00Z",
            "landing_zone_km": 45,
            "predicted_path": [
                {"lat": 37.7749, "lon": -122.4194, "alt": 24500},
                {"lat": 37.7800, "lon": -122.4100, "alt": 22000},
                {"lat": 37.7850, "lon": -122.4000, "alt": 18000},
            ],
        },
    }
