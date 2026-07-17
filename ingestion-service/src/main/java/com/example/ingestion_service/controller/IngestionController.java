package com.example.ingestion_service.controller;

import com.example.ingestion_service.scheduler.IngestionScheduler;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/ingest")
public class IngestionController {

    private final IngestionScheduler scheduler;

    public IngestionController(IngestionScheduler scheduler) {
        this.scheduler = scheduler;
    }

    @PostMapping("/trigger")
    public ResponseEntity<Map<String, Object>> triggerIngestion() {
        scheduler.triggerIngestionProcess();
        return ResponseEntity.ok(Map.of(
                "status", "SUCCESS",
                "message", "Ingestion process triggered manually"
        ));
    }

    @GetMapping("/status")
    public ResponseEntity<Map<String, Object>> getStatus() {
        return ResponseEntity.ok(Map.of(
                "schedulerEnabled", scheduler.isSchedulerEnabled(),
                "processedPricesCount", scheduler.getProcessedPricesCount(),
                "processedNewsCount", scheduler.getProcessedNewsCount()
        ));
    }

    @PostMapping("/scheduler/toggle")
    public ResponseEntity<Map<String, Object>> toggleScheduler(@RequestParam boolean enable) {
        scheduler.setSchedulerEnabled(enable);
        return ResponseEntity.ok(Map.of(
                "schedulerEnabled", scheduler.isSchedulerEnabled(),
                "message", "Scheduler status updated"
        ));
    }
}
