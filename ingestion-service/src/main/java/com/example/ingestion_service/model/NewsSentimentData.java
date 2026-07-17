package com.example.ingestion_service.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class NewsSentimentData {
    private String ticker;
    private String title;
    private String url;
    private String source;
    private double sentimentScore;
    private double confidenceScore;
    private LocalDateTime timestamp;
}
