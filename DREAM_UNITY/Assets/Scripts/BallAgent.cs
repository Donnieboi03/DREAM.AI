using Unity.MLAgents;
using Unity.MLAgents.Actuators;
using Unity.MLAgents.Sensors;
using UnityEngine;

public class BallAgent : Agent
{
    [Header("Time Scale Control")]
    [Range(0.1f, 50f)]
    public float desiredTimeScale = 1f;
    private int ep = 0;
    public Transform target;
    public float forceMultiplier = 10f;
    public float arenaSize = 7f;
    public float successDist = 0.5f;
    private float prevDist;

    private Rigidbody rb;

    public override void Initialize()
    {
        Time.timeScale = 0;
        prevDist = Vector3.Distance(transform.localPosition, target.localPosition);
        rb = GetComponent<Rigidbody>();
    }

    public override void OnEpisodeBegin()
    {
        ep++;
        Debug.Log("Episode: " + ep);
        Time.timeScale = desiredTimeScale;
        // Reset agent
        rb.linearVelocity = Vector3.zero;
        rb.angularVelocity = Vector3.zero;
        transform.localPosition = new Vector3(Random.Range(-arenaSize, arenaSize), 0.5f, Random.Range(-arenaSize, arenaSize));

        // Reset target
        target.localPosition = new Vector3(Random.Range(-arenaSize, arenaSize), 0.5f, Random.Range(-arenaSize, arenaSize));
    }

    public override void CollectObservations(VectorSensor sensor)
    {
        Vector3 delta = target.localPosition - transform.localPosition;

        // Relative target position (x,z) + agent velocity (x,z)
        sensor.AddObservation(delta.x);
        sensor.AddObservation(delta.z);
        sensor.AddObservation(rb.linearVelocity.x);
        sensor.AddObservation(rb.linearVelocity.z);
    }

    public override void OnActionReceived(ActionBuffers actions)
    {

        float ax = Mathf.Clamp(actions.ContinuousActions[0], -1f, 1f);
        float az = Mathf.Clamp(actions.ContinuousActions[1], -1f, 1f);

        rb.AddForce(new Vector3(ax, 0f, az) * forceMultiplier, ForceMode.Acceleration);

        float dist = Vector3.Distance(transform.localPosition, target.localPosition);

        AddReward(prevDist - dist);  // improvement
        prevDist = dist;

        AddReward(-0.001f);

        if (transform.localPosition.y < -1f)
        {
            AddReward(-1.0f);   // or -2.0f
            EndEpisode();
            return;
        }

        if (dist < successDist)
        {
            AddReward(+1.0f);
            EndEpisode();
        }

    }
}
