package com.example.promptstudio;
import org.springframework.beans.factory.annotation.Value; import org.springframework.http.*; import org.springframework.web.bind.annotation.*; import org.springframework.web.client.RestClient;
@RestController @RequestMapping("/api/v1") public class ExperimentController {
 private final RestClient client;
 public ExperimentController(@Value("${studio.python-url:http://localhost:8000}") String url){client=RestClient.builder().baseUrl(url).build();}
 @PostMapping("/experiments") public ResponseEntity<String> run(@RequestBody String body){return ResponseEntity.ok(client.post().uri("/api/v1/experiments").contentType(MediaType.APPLICATION_JSON).body(body).retrieve().body(String.class));}
 @GetMapping("/experiments/{id}") public ResponseEntity<String> get(@PathVariable String id){return ResponseEntity.ok(client.get().uri("/api/v1/experiments/"+id).retrieve().body(String.class));}
 @GetMapping("/analytics") public ResponseEntity<String> analytics(){return ResponseEntity.ok(client.get().uri("/api/v1/analytics").retrieve().body(String.class));}
}
