import time
import threading
from typing import Dict, Tuple
from collections import defaultdict
from app.core.config import settings


class GlobalDDoSProtector:
    """
    High-Performance Anti-DDoS, Layer-7 Flood, and Sliding-Window Rate Limiter.
    
    Architecture:
    1. Global Request Rate Limiting (Protects CPU/RAM exhaustion against L7 flooding).
    2. Endpoint-Specific Strict Limiting (e.g., /auth/login credential stuffing prevention).
    3. Auto-Jailing (Bans offending IPs making abnormal bursts of requests for 15+ minutes).
    4. Auto-Garbage Collection (Cleans up expired timestamps in memory periodically).
    5. Whitelist support for Loopback/Dev proxies.
    """

    def __init__(self):
        self._lock = threading.Lock()
        
        # General Traffic: IP -> list of request timestamps within 60s
        self._ip_general_requests: Dict[str, list] = defaultdict(list)
        
        # Auth Strict Traffic: IP -> list of request timestamps
        self._ip_auth_requests: Dict[str, list] = defaultdict(list)
        
        # Jailed IPs: IP -> banned_until timestamp
        self._jailed_ips: Dict[str, float] = {}
        
        # Failed Logins: IP -> (failure_count, lockout_expiry)
        self._ip_failed_logins: Dict[str, Tuple[int, float]] = {}

        # Default Protection Parameters
        self.GLOBAL_WINDOW_SECONDS = 60
        self.GLOBAL_MAX_REQUESTS_PER_MIN = 120  # Max 120 requests/minute per IP
        self.BURST_TOLERANCE_PER_10S = 40       # Max 40 requests per 10 seconds
        self.JAIL_TIME_SECONDS = 900             # 15 Minutes ban for flooding
        
        self.AUTH_WINDOW_SECONDS = 60
        self.AUTH_MAX_REQUESTS = 12             # Max 12 login tries per minute

        # Loopback whitelist
        self.WHITELISTED_IPS = {"127.0.0.1", "localhost", "::1"}

    def is_ip_jailed(self, ip: str) -> Tuple[bool, int]:
        """Check if an IP has been jailed due to aggressive flood/DDoS attempt."""
        if ip in self.WHITELISTED_IPS:
            return False, 0

        now = time.time()
        with self._lock:
            if ip in self._jailed_ips:
                banned_until = self._jailed_ips[ip]
                if now < banned_until:
                    return True, int(banned_until - now)
                else:
                    del self._jailed_ips[ip]
        return False, 0

    def check_general_rate_limit(self, ip: str) -> Tuple[bool, int, str]:
        """
        DDoS Flood Shield for all HTTP requests:
        Checks both 10-second burst and 60-second aggregate thresholds.
        Returns: (is_blocked, retry_after, reason)
        """
        if ip in self.WHITELISTED_IPS:
            return False, 0, ""

        now = time.time()
        with self._lock:
            # 1. Check if already jailed
            if ip in self._jailed_ips:
                banned_until = self._jailed_ips[ip]
                if now < banned_until:
                    return True, int(banned_until - now), "IP temporarily banned for aggressive flooding."
                else:
                    del self._jailed_ips[ip]

            # 2. Clean sliding window
            timestamps = [t for t in self._ip_general_requests[ip] if now - t < self.GLOBAL_WINDOW_SECONDS]
            self._ip_general_requests[ip] = timestamps

            # 3. Burst Check (within last 10 seconds)
            recent_burst = [t for t in timestamps if now - t <= 10]
            if len(recent_burst) >= self.BURST_TOLERANCE_PER_10S:
                # Instant 15-minute Jail
                self._jailed_ips[ip] = now + self.JAIL_TIME_SECONDS
                return True, self.JAIL_TIME_SECONDS, "Layer-7 burst flood detected. IP jailed for 15 minutes."

            # 4. Standard 60-second limit
            if len(timestamps) >= self.GLOBAL_MAX_REQUESTS_PER_MIN:
                retry_after = int(self.GLOBAL_WINDOW_SECONDS - (now - timestamps[0]))
                return True, max(retry_after, 1), "Too many requests. Rate limit exceeded."

            self._ip_general_requests[ip].append(now)
            return False, 0, ""

    def is_ip_rate_limited(self, ip: str) -> Tuple[bool, int]:
        """
        Legacy & Auth-specific rate limit check.
        Ensures strict limits on sensitive endpoints (e.g. Login).
        """
        if ip in self.WHITELISTED_IPS:
            return False, 0

        now = time.time()
        with self._lock:
            if ip in self._jailed_ips:
                banned_until = self._jailed_ips[ip]
                if now < banned_until:
                    return True, int(banned_until - now)
                else:
                    del self._jailed_ips[ip]

            timestamps = [t for t in self._ip_auth_requests[ip] if now - t < self.AUTH_WINDOW_SECONDS]
            self._ip_auth_requests[ip] = timestamps

            if len(timestamps) >= self.AUTH_MAX_REQUESTS:
                retry_after = int(self.AUTH_WINDOW_SECONDS - (now - timestamps[0]))
                return True, max(retry_after, 1)

            self._ip_auth_requests[ip].append(now)
            return False, 0

    def record_ip_failure(self, ip: str) -> None:
        """Records a failed credential attempt."""
        if ip in self.WHITELISTED_IPS:
            return

        now = time.time()
        with self._lock:
            fails, _ = self._ip_failed_logins.get(ip, (0, 0))
            fails += 1
            if fails >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
                lockout_time = now + (settings.LOCKOUT_DURATION_MINUTES * 60)
                self._ip_failed_logins[ip] = (fails, lockout_time)
            else:
                self._ip_failed_logins[ip] = (fails, 0)

    def reset_ip_failures(self, ip: str) -> None:
        """Resets failed attempts on valid login."""
        with self._lock:
            self._ip_failed_logins.pop(ip, None)
            self._ip_auth_requests.pop(ip, None)


# Singleton Global Protector Instance
limiter = GlobalDDoSProtector()
