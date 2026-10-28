# Presentation Transcript

## Slide 1

Hi, I'm Stelios, and today I will be presenting IYPT 2026 problem #6: The Flipo Flip.

## Slide 2

The problem statement reads: "A Flipo Flip toy can roll for multiple turns even though its shape is not circular. Investigate how its motion depends on parameters such as geometry and initial release conditions." Our goal in this presentation is to understand the geometry of the toy, develop a theoretical model that connects relevant parameters and describes the motion of the toy, and test our model and assumptions with experimental measurements.

## Slide 3

Let's start with the geometry of the toy. To understand it, we will use a solid object called the Steinmetz solid, also known as a bicylinder. The Steinmetz solid is the body formed by the intersection of two cylinders of equal radius R at right angles.

## Slide 4

The toy is constructed by taking the outer sections of a Steinmetz solid — the part highlighted here on top, and an identical one from the bottom — and joining them with a thin square prism with rounded edges. Since both cylinders share the same axis of rotation during the toy's motion, the total moment of inertia about that axis is the sum of the two individual moments of inertia, equal to mR², where m is the mass of each cylinder and R is its radius. Because this surface comes from a Steinmetz solid, when the toy rolls on it the contact geometry is identical to that of a cylinder of radius R rolling.

## Slide 5

Now, let's move on to the categorisation of the phases of motion of the toy. When the toy is rolling on a flat surface, we can describe the motion as a sequence of three repeating phases: Pure patch rolling, Ridge switch, and Patch switch.

## Slide 6

Pure patch rolling is the phase in which the toy rolls along its large curved surface — in other words, when the contact point remains on one cylindrical patch. As I mentioned, during this phase the contact geometry is equivalent to that of a circular cylinder of radius R. A key assumption of our model is the no-slip condition: the velocity of the centre of mass equals the angular velocity times the radius — which is required for rolling to occur.

## Slide 7

During this rolling motion, the only form of energy dissipation we can observe is from the rolling resistance between the Flipo Flip and the floor. The rolling resistance force is equal to the rolling resistance coefficient multiplied by the weight of the bicylinder. The work done by it is the force times the distance travelled during pure patch rolling, and that distance equals πR/2. Dissipation from aerodynamic drag is negligible given the small velocities the toy achieves. It is also worth noting that rolling resistance only accounts for the dissipation of translational energy; the remaining rotational energy is dissipated by other mechanisms, such as switching dissipation, for the toy to eventually come to rest.

## Slide 8

Using the rolling resistance force, we can find how the translational velocity u(t) is reduced during pure patch rolling. It equals the initial velocity minus the acceleration multiplied by the time elapsed during pure patch rolling, where the acceleration is the rolling resistance force divided by the effective mass of the toy. The effective mass is the physical mass plus a term related to its rolling inertia.

## Slide 9

Let's move on to the ridge switch. It happens during pure patch rolling, when the contact point passes through the centre of the curved surface — the contact point between the two cylinders, which we call the ridge. The dissipation and mechanics at this point are already accounted for in pure patch rolling, and nothing changes here; it is just worth noting.

## Slide 10

The third phase of the motion is the patch switch. During this phase, the contact point is on one of the edges of the square prism at the bottom, or on the entire flat surface — which occurs only for an instant as it transitions between them. This phase sits between the end of pure patch rolling on one cylindrical patch and the start of pure patch rolling on the other. When the contact point reaches the square edge between patches, the admissible pure-rolling direction jumps by 90 degrees. Two things can happen: if there is sufficient friction, the toy will smoothly reorient over a finite time and continue rolling on the new patch, with some additional energy loss.

> **[If asked]:** The 90-degree change is because the CM velocity was pointing toward the ground, and now it points to the left — that's 90 degrees.

## Slide 11

But if friction is insufficient to provide the tangential impulse required for an instantaneous turn, the toy will slip and yaw, which dissipates energy quickly and prevents any additional flips.

## Slide 12

You cannot instantaneously change the CM velocity vector from (u,0) to (0,u) — the 90-degree change I've been referring to — unless impulses of the right magnitude and direction are applied. An instantaneous 90-degree reorientation requires a large tangential impulse and a corresponding change in angular momentum. To quantify this, suppose the Flipo Flip is rolling along the x-axis and we want to redirect its CM velocity to the y-axis. We only care about the magnitude of the change, which is why we chose two orientations differing by 90 degrees. We start with the change in momentum, which is mass times the difference of the CM velocity vectors for a 90-degree change. From this we find the magnitude of that change: the square root of the sum of squares of the initial and final momenta. We then find the change in angular momentum as the square root of the sum of squares of the initial and final angular momenta — each equal to their respective moment of inertia times angular velocity. Converting the change in angular momentum to the required impulse by dividing by R, and summing with the translational impulse, gives us the total required impulse J_req, which works out to the square root of 2 times velocity times the effective mass.

## Slide 13

The only force that can provide this impulse is friction. We can therefore define a dimensionless number Λ (Lambda) that compares the available frictional impulse to the required impulse for the patch switch. If Λ is much smaller than one, most of the energy will be lost during the switch and the motion will stop there. Generally, Λ is between 0 and 1, and it controls how much energy is dissipated during each patch switch.

## Slide 14

Let's move on to the full motion analysis. We have the equations derived for pure patch rolling, now rewritten, alongside the patch switch dissipation equations. For pure patch rolling, the acceleration equals minus the friction force divided by the effective mass, which equals k, and after some calculations equals the rolling friction coefficient times g over 2. We also have the function that describes how velocity decreases during pure rolling. For patch switch dissipation, the velocity right after the patch switch equals the velocity before the switch times (1 − Λ). This is how Λ controls energy dissipation at each patch switch. If we assume Λ is constant across all switches, we can write an expression for the velocity at the n-th switch, accounting for all preceding patch switches and rolling phases.

## Slide 15

In each pure patch rolling interval, velocity evolves linearly, and is then multiplied by a factor less than one at each patch switch. Velocity can only reach zero during the linear decrease, not during the proportional drop of a patch switch, and from this we get the equation for t_stop — the time at which the Flipo Flip stops rolling.

## Slide 16

The toy stops at the smallest nonnegative integer n satisfying u_n < kΔt. To get n in closed form, we solve the equality, which gives the following expression for continuous n.

## Slide 17

These are the equations I have described, and from them we can theoretically predict the number of patch switches the Flipo Flip will make before stopping. These are the equations used for the theoretical predictions in the plots you will see in the experiments section.

## Slide 18

Now that we have completed the theoretical model, let's move on to our experiments. For our setup, we used 6 Flipo Flips with different materials, masses, and dimensions, a laser distance meter, Tracker video analysis software, and a force gauge to apply different forces to the toy.

## Slide 19

In order for our theoretical model to predict the number of flips before motion stops, we experimentally measured the effective mass, the patch switch time, and the rolling friction coefficient separately for each Flipo Flip.

## Slide 20

The first part of our analysis has to do with force application. We measured the number of flips the toy could do before slipping or stopping as a function of initial velocity, but how that velocity is applied matters. We may apply a force in any of the visible locations,

## Slide 21

and only some of them will initiate the motion.

## Slide 22

Here, we can see all the locations the initial force was applied during our experiments, but only the green ones actually allowed the motion to start.

## Slide 23

For each of the 6 Flipo Flips, the experiment went as follows: the Flipo Flip was placed upright, and a force was applied to the centre of the surface above the ridge using the force gauge. We used that force to give the toy an initial velocity, measured with Tracker. We then recorded the number of flips for each initial velocity, producing the (initial velocity, number of flips) pairs visible on the diagram. This process was repeated until ten such pairs were obtained. Each Flipo Flip has 10 data points for each of two different surfaces — in other words, 20 experimental values per Flipo Flip, ten on one surface type and ten on another, in order to vary the rolling friction coefficient. We used integer initial velocities from 2 m/s up to 10 m/s, plus 15 m/s. Here you can see the two graphs corresponding to the two surfaces for each Flipo Flip, with their experimentally measured friction coefficients, and a plot of the experimental and theoretical data points.

## Slide 24

Our model generally overpredicts or matches the number of flips observed in each experiment. This is likely because of additional losses not captured in the model, such as air resistance or minor deformations. Another contributing factor is the simplifying assumptions we made: we keep Λ constant, whereas in practice it would decrease, and we treat t_switch as constant, whereas it would increase as the velocity drops — each patch switch taking longer and therefore dissipating more energy. The no-slip assumption also plays a role: since we assume the toy never slips, it may slip earlier than its available energy would otherwise permit, which produces the gap between the theoretical and experimental data.

## Slide 25

We can also see that there is a critical velocity for each Flipo Flip, above which the toy does no flips at all, while the model predicts an increasing number. We will discuss that shortly.

## Slide 26

We can also see that a smaller friction coefficient leads to a larger error in our model. We believe this is related to the no-slip assumption: when the rolling friction coefficient is smaller, the toy is more likely to slip before it would otherwise stop based on its available energy alone.

## Slide 27

As you can see, the trends we discussed are consistent across all the Flipo Flips.

## Slide 28

And this is our last Flipo Flip, which also has the smallest critical velocity. Time to address the elephant in the room.

## Slide 29

Why are there cases where 0 flips are done? In other words, why does a critical velocity exist? It's also due to the no-slip condition.

## Slide 30

To model the toy's motion, we assumed it actually rolls. But sometimes the no-slip condition cannot hold from the very start, because the initial velocity is too high for the toy to maintain ground contact, and it gets launched into the air.

## Slide 31

Here's our bibliography.

## Slide 32

And thank you very much for your attention!

## Slide 33

*(No spoken text.)*
