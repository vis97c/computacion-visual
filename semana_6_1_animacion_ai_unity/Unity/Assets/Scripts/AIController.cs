using UnityEngine;
using UnityEngine.AI;

public class AIController : MonoBehaviour
{
    public enum AIState { Idle, Patrol, Chase }

    [Header("FSM")]         public AIState currentState = AIState.Idle;
    [Header("Patrol")]      public Transform[] waypoints;
    [Header("Detection")]   public float detectionRadius = 10f;
                              public float loseRadius = 15f;
                              public Transform player;
    [Header("Idle")]        public float idleDuration = 2f;

    int _wpIdx;
    float _timer;
    NavMeshAgent _agent;
    Animator _anim;

    void Start()
    {
        _agent = GetComponent<NavMeshAgent>();
        _anim  = GetComponent<Animator>();
        if (!player)
        {
            var p = GameObject.FindWithTag("Player");
            if (p) player = p.transform;
        }
        SetIdle();
    }

    void Update()
    {
        switch (currentState)
        {
            case AIState.Idle:   RunIdle();   break;
            case AIState.Patrol: RunPatrol(); break;
            case AIState.Chase:  RunChase();  break;
        }
        if (_anim)
        {
            _anim.SetFloat("Speed", _agent.velocity.magnitude);
            _anim.SetInteger("State", (int)currentState);
        }
    }

    void RunIdle()
    {
        _agent.isStopped = true;
        _timer += Time.deltaTime;
        if (_timer >= idleDuration) SetPatrol();
    }

    void RunPatrol()
    {
        _agent.isStopped = false;
        if (!_agent.pathPending && _agent.remainingDistance < 0.5f)
        {
            _timer += Time.deltaTime;
            if (_timer >= idleDuration)
            {
                _timer = 0f;
                _wpIdx = (_wpIdx + 1) % waypoints.Length;
                _agent.SetDestination(waypoints[_wpIdx].position);
            }
        }
        if (InRange(detectionRadius)) SetChase();
    }

    void RunChase()
    {
        _agent.isStopped = false;
        if (player) _agent.SetDestination(player.position);
        if (!InRange(loseRadius)) SetPatrol();
    }

    void SetIdle()
    {
        currentState = AIState.Idle;
        _timer = 0f;
        _agent.isStopped = true;
    }

    void SetPatrol()
    {
        currentState = AIState.Patrol;
        _timer = 0f;
        _agent.speed = 3.5f;
        if (waypoints != null && waypoints.Length > 0)
            _agent.SetDestination(waypoints[_wpIdx].position);
    }

    void SetChase()
    {
        currentState = AIState.Chase;
        _timer = 0f;
        _agent.speed = 5f;
    }

    bool InRange(float r)
        => player && Vector3.Distance(transform.position, player.position) < r;

    void OnDrawGizmosSelected()
    {
        Gizmos.color = new Color(1,1,0,.25f);
        Gizmos.DrawWireSphere(transform.position, detectionRadius);
        Gizmos.color = new Color(1,0,0,.15f);
        Gizmos.DrawWireSphere(transform.position, loseRadius);
        if (waypoints == null) return;
        Gizmos.color = Color.cyan;
        for (int i = 0; i < waypoints.Length; i++)
        {
            if (!waypoints[i]) continue;
            Gizmos.DrawSphere(waypoints[i].position, .35f);
            Gizmos.DrawLine(waypoints[i].position,
                waypoints[(i + 1) % waypoints.Length].position);
        }
    }
}