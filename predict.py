"""
Predict the actual hand position by taking all 
results from the detectors into account.
Also, consider the confidence level of each detector.
"""


from hand_pos import HandPos, Outline
import numpy
import rectangle

def get_bins(rectangles):
  """
  Get bins of overlapping rectangles.
  All rectangles which overlap by a certain percentage will be put
  into the same bin.
  """
  bins = [ [r] for r in rectangles]
  for i, rect1 in enumerate(rectangles):
    for rect2 in rectangles:
      # Extract values from (rect_pos, probability) tuples
      r1, p1 = rect1
      r2, p2 = rect2
      if not numpy.array_equal(r1,r2) and rectangle.intersect_percentage(r1, r2) > 0.5:
        bins[i].append(rect2)
  return bins

def positions_overlap(positions):
  """
  Get the largest set of overlapping rectangles.
  """
  hands = positions.values()
  if len(hands) < 1:
    return []

  rectangles = []
  for hand in hands:
    if hand.outline == Outline.ELLIPSE:
      # Convert to rectangle to calculate intersections
      pos = rectangle.get_bounding_rect(hand.pos)
    else:
      pos = hand.pos
    # Store results for further analysis
    rectangles.append((pos, hand.prob))

  bins = get_bins(rectangles)
  max_bins = sorted(bins, key=lambda bin: len(bin), reverse=True)
  return max_bins[0]

def average_weighted(rects):
  """
  Calculate an average rectangle from all input rectangles.
  Use the probability as a weight to build the average, e.g.
  avg = sum([prob*rect for rect,prob in rects]) / len(rects)
  """
  sum_p = sum([p for r,p in rects])
  products_x1 = [r[0]*p for r,p in rects]
  products_y1 = [r[1]*p for r,p in rects]
  products_x2 = [r[2]*p for r,p in rects]
  products_y2 = [r[3]*p for r,p in rects]
  avg_x1 = int(sum(products_x1) / sum_p)
  avg_y1 = int(sum(products_y1) / sum_p)
  avg_x2 = int(sum(products_x2) / sum_p)
  avg_y2 = int(sum(products_y2) / sum_p)
  r = [avg_x1, avg_y1, avg_x2, avg_y2]
  r = rectangle.offset(r, (0,-20))
  avg_p = sum_p / len(rects)
  return HandPos(pos=r, prob=avg_p)

def max_prob(positions):
  """
  Get position with largest probability of correctness
  """
  max_h = HandPos()
  for h in positions.itervalues():
    if h.prob > max_h.prob:
      max_h = h
  return max_h
